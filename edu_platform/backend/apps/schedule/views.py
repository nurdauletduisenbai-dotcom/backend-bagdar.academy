from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.common.viewsets import CourseScopedViewSet
from apps.courses.access import confirmed_children_ids, managed_course_ids
from apps.courses.models import Enrollment, Group

from .models import Attendance, Session
from .services import ScheduleService, group_student_ids

# ---------- Сериализаторы ----------


class ClassSessionSerializer(serializers.ModelSerializer):
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all())
    course_id = serializers.IntegerField(source='group.course_id', read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True)

    class Meta:
        model = Session
        fields = ('id', 'group', 'group_name', 'course_id', 'title', 'start_time', 'end_time', 'location',
                  'online_meeting_url', 'lesson', 'is_canceled', 'created_at')
        read_only_fields = ('id', 'created_at')

    def validate(self, attrs):
        group = attrs.get('group') or self.instance.group
        start = attrs.get('start_time') or self.instance.start_time
        end = attrs.get('end_time') or self.instance.end_time
        lesson = attrs.get('lesson', self.instance.lesson if self.instance else None)
        if lesson and lesson.section.course_id != group.course_id:
            raise serializers.ValidationError({'lesson': 'Урок из другого курса.'})
        if not attrs.get('is_canceled', self.instance.is_canceled if self.instance else False):
            ScheduleService.validate_slot(group, start, end, exclude_id=self.instance.id if self.instance else None)
        return attrs


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    session_title = serializers.CharField(source='session.title', read_only=True)
    session_start = serializers.DateTimeField(source='session.start_time', read_only=True)

    class Meta:
        model = Attendance
        fields = ('id', 'session', 'session_title', 'session_start', 'student', 'student_name', 'status', 'notes')
        read_only_fields = fields


class AttendanceRecordSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    status = serializers.ChoiceField(choices=Attendance.Status.choices)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=255)


class MarkAttendanceSerializer(serializers.Serializer):
    records = AttendanceRecordSerializer(many=True)


class GroupSerializer(serializers.ModelSerializer):
    students_count = serializers.SerializerMethodField()

    class Meta:
        model = Group
        fields = ('id', 'course', 'name', 'max_students', 'is_active', 'students_count', 'created_at')
        read_only_fields = ('id', 'created_at')

    def get_students_count(self, obj) -> int:
        return len(group_student_ids(obj))


class GroupStudentSerializer(serializers.Serializer):
    student_id = serializers.IntegerField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    access_until = serializers.DateTimeField()


# ---------- Views ----------


@extend_schema_view(list=extend_schema(summary='Группы (потоки) курсов', parameters=[OpenApiParameter('course', int)]))
@extend_schema(tags=['schedule'])
class GroupViewSet(CourseScopedViewSet):
    queryset = Group.objects.select_related('course').order_by('course_id', 'name')
    serializer_class = GroupSerializer
    filterset_fields = ['course', 'is_active']
    pagination_class = None

    def filter_for_learner(self, qs):
        user = self.request.user
        return qs.filter(Q(course_id__in=self.managed_ids()) | Q(enrollments__student=user)).distinct()

    @extend_schema(summary='Ученики группы', responses=GroupStudentSerializer(many=True))
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        group = self.get_object()
        self.check_manage(group.course)
        rows = Enrollment.objects.filter(
            group=group, status=Enrollment.Status.ACTIVE, access_until__gte=timezone.now()
        ).select_related('student')
        return Response([
            {'student_id': e.student_id, 'email': e.student.email, 'full_name': e.student.get_full_name(),
             'access_until': e.access_until}
            for e in rows
        ])


@extend_schema_view(
    list=extend_schema(
        summary='Расписание: свои группы (ученик), группы детей (родитель), курсы (преподаватель)',
        parameters=[OpenApiParameter('group', int), OpenApiParameter('course', int),
                    OpenApiParameter('date_from', str, description='ISO datetime'),
                    OpenApiParameter('date_to', str, description='ISO datetime')],
    ),
    create=extend_schema(summary='Создать занятие (проверяется пересечение по времени)'),
)
@extend_schema(tags=['schedule'])
class SessionViewSet(CourseScopedViewSet):
    queryset = Session.objects.select_related('group__course').order_by('start_time')
    serializer_class = ClassSessionSerializer
    course_path = 'group__course'
    filterset_fields = ['group', 'is_canceled']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Session.objects.none()
        user = self.request.user
        org_id = getattr(self.request, 'org_id', None)
        now = timezone.now()
        learner_groups = Enrollment.objects.filter(
            Q(student=user) | Q(student_id__in=confirmed_children_ids(user)),
            status=Enrollment.Status.ACTIVE, access_until__gte=now, group__isnull=False,
        ).values_list('group_id', flat=True)
        curator_orgs = user.memberships.filter(is_active=True, role__in=['curator', 'admin']).values_list('org_id', flat=True)
        qs = self.queryset.filter(
            Q(group__course_id__in=managed_course_ids(user, org_id))
            | Q(group__course__org_id__in=curator_orgs)
            | Q(group_id__in=learner_groups)
        ).distinct()

        params = self.request.query_params
        if params.get('course', '').isdigit():
            qs = qs.filter(group__course_id=params['course'])
        if params.get('date_from') and parse_datetime(params['date_from']):
            qs = qs.filter(start_time__gte=parse_datetime(params['date_from']))
        if params.get('date_to') and parse_datetime(params['date_to']):
            qs = qs.filter(start_time__lte=parse_datetime(params['date_to']))
        return qs

    def course_from_data(self, validated_data):
        return validated_data['group'].course

    def perform_update(self, serializer):
        was_canceled = serializer.instance.is_canceled
        super().perform_update(serializer)
        if serializer.instance.is_canceled and not was_canceled:
            ScheduleService.notify_canceled(serializer.instance)

    @extend_schema(methods=['get'], summary='Посещаемость занятия (преподаватель)',
                   responses=AttendanceSerializer(many=True))
    @extend_schema(methods=['put'], summary='Отметить посещаемость (пакетно)', request=MarkAttendanceSerializer,
                   responses=AttendanceSerializer(many=True))
    @action(detail=True, methods=['get', 'put'])
    def attendance(self, request, pk=None):
        session = self.get_object()
        self.check_manage(session.group.course)
        if request.method == 'PUT':
            serializer = MarkAttendanceSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            ScheduleService.mark_attendance(session, serializer.validated_data['records'])
        items = session.attendances.select_related('student', 'session')
        return Response(AttendanceSerializer(items, many=True).data)


@extend_schema_view(list=extend_schema(
    summary='Посещаемость: своя, детей или учеников своих курсов',
    parameters=[OpenApiParameter('student', int), OpenApiParameter('status', str)],
))
@extend_schema(tags=['schedule'])
class AttendanceViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['student', 'status', 'session']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Attendance.objects.none()
        user = self.request.user
        return Attendance.objects.select_related('student', 'session').filter(
            Q(student=user)
            | Q(student_id__in=confirmed_children_ids(user))
            | Q(session__group__course_id__in=managed_course_ids(user, getattr(self.request, 'org_id', None)))
        ).order_by('-session__start_time').distinct()
