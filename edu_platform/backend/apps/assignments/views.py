from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.common.files import protected_file_response
from apps.common.viewsets import CourseScopedViewSet
from apps.content.models import Lesson
from apps.courses.access import can_manage_course, confirmed_children_ids, managed_course_ids

from .models import Assignment, AssignmentSubmission
from .services import AssignmentService

# ---------- Сериализаторы ----------


class SubmissionSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.get_full_name', read_only=True)
    student_email = serializers.EmailField(source='student.email', read_only=True)
    assignment_title = serializers.CharField(source='assignment.title', read_only=True)
    has_file = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = AssignmentSubmission
        fields = ('id', 'assignment', 'assignment_title', 'student', 'student_name', 'student_email',
                  'text_content', 'file_url', 'has_file', 'download_url', 'status', 'submitted_at', 'is_late',
                  'score', 'feedback', 'graded_at', 'can_resubmit')
        read_only_fields = fields

    def get_has_file(self, obj) -> bool:
        return bool(obj.file)

    def get_download_url(self, obj) -> str | None:
        return f'/api/v1/submissions/{obj.id}/download/' if obj.file else None


class AssignmentSerializer(serializers.ModelSerializer):
    lesson = serializers.PrimaryKeyRelatedField(queryset=Lesson.objects.all())
    course_id = serializers.IntegerField(source='lesson.section.course_id', read_only=True)
    my_submission = serializers.SerializerMethodField()
    submissions_count = serializers.SerializerMethodField()
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = ('id', 'lesson', 'course_id', 'title', 'description', 'deadline', 'max_score', 'accept_late',
                  'is_overdue', 'my_submission', 'submissions_count', 'created_at')
        read_only_fields = ('id', 'created_at')

    def get_is_overdue(self, obj) -> bool:
        return obj.deadline < timezone.now()

    def get_my_submission(self, obj) -> dict | None:
        user = self.context['request'].user
        sub = obj.submissions.filter(student=user).first()
        return SubmissionSerializer(sub, context=self.context).data if sub else None

    def get_submissions_count(self, obj) -> int | None:
        managed = self.context.get('managed_course_ids', set())
        return obj.submissions.count() if obj.lesson.section.course_id in managed else None


class SubmitSerializer(serializers.Serializer):
    text_content = serializers.CharField(required=False, allow_blank=True)
    file = serializers.FileField(required=False)
    file_url = serializers.URLField(required=False, allow_blank=True)


class GradeSubmissionSerializer(serializers.Serializer):
    score = serializers.FloatField(min_value=0)
    feedback = serializers.CharField(required=False, allow_blank=True, default='')
    can_resubmit = serializers.BooleanField(default=False, help_text='Вернуть на доработку')


# ---------- Views ----------


@extend_schema_view(
    list=extend_schema(summary='Домашние задания', parameters=[OpenApiParameter('lesson', int), OpenApiParameter('course', int)]),
    create=extend_schema(summary='Создать задание (ученики курса получат уведомление)'),
)
@extend_schema(tags=['assignments'])
class AssignmentViewSet(CourseScopedViewSet):
    queryset = Assignment.objects.select_related('lesson__section__course')
    serializer_class = AssignmentSerializer
    course_path = 'lesson__section__course'
    filterset_fields = ['lesson']
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get_queryset(self):
        qs = super().get_queryset()
        course_id = self.request.query_params.get('course')
        if course_id and course_id.isdigit():
            qs = qs.filter(lesson__section__course_id=course_id)
        return qs

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.request and self.request.user.is_authenticated:
            ctx['managed_course_ids'] = self.managed_ids()
        return ctx

    def course_from_data(self, validated_data):
        return validated_data['lesson'].section.course

    def save_create(self, serializer):
        assignment = serializer.save(created_by=self.request.user)
        AssignmentService.notify_new(assignment)

    @extend_schema(summary='Сдать задание (текст, файл и/или ссылка; multipart для файла)',
                   request={'multipart/form-data': SubmitSerializer, 'application/json': SubmitSerializer},
                   responses={201: SubmissionSerializer})
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        assignment = self.get_object()
        serializer = SubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = AssignmentService.submit(assignment, request.user, **serializer.validated_data)
        return Response(SubmissionSerializer(submission).data, status=status.HTTP_201_CREATED)

    @extend_schema(summary='Сдачи по заданию (преподаватель)', responses=SubmissionSerializer(many=True))
    @action(detail=True, methods=['get'])
    def submissions(self, request, pk=None):
        assignment = self.get_object()
        self.check_manage(AssignmentService.course_of(assignment))
        qs = assignment.submissions.select_related('student', 'assignment')
        page = self.paginate_queryset(qs)
        return self.get_paginated_response(SubmissionSerializer(page, many=True).data)


@extend_schema_view(
    list=extend_schema(
        summary='Сдачи работ: свои (ученик), детей (родитель), курсов (преподаватель)',
        parameters=[OpenApiParameter('assignment', int), OpenApiParameter('student', int),
                    OpenApiParameter('status', str)],
    ),
)
@extend_schema(tags=['assignments'])
class SubmissionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['assignment', 'student', 'status']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return AssignmentSubmission.objects.none()
        user = self.request.user
        return AssignmentSubmission.objects.select_related(
            'student', 'assignment__lesson__section__course'
        ).filter(
            Q(student=user)
            | Q(student_id__in=confirmed_children_ids(user))
            | Q(assignment__lesson__section__course_id__in=managed_course_ids(user, getattr(self.request, 'org_id', None)))
        ).distinct()

    @extend_schema(summary='Оценить работу (преподаватель курса)', request=GradeSubmissionSerializer,
                   responses=SubmissionSerializer)
    @action(detail=True, methods=['post'])
    def grade(self, request, pk=None):
        submission = self.get_object()
        if not can_manage_course(request.user, AssignmentService.course_of(submission.assignment)):
            raise PermissionDenied('Оценивать работы может преподаватель курса.')
        serializer = GradeSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        submission = AssignmentService.grade(submission, request.user, **serializer.validated_data)
        return Response(SubmissionSerializer(submission).data)

    @extend_schema(summary='Скачать файл работы', responses={(200, 'application/octet-stream'): bytes})
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        submission = self.get_object()
        return protected_file_response(submission.file, f'{submission.assignment.title}-{submission.student_id}')
