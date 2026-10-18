from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, permissions, serializers, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.courses.access import can_manage_course, is_org_admin, viewable_course_ids
from apps.courses.models import Course

from .models import Announcement, Notification, NotificationPreference
from .services import NotificationService

# ---------- Сериализаторы ----------


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('id', 'type', 'title', 'message', 'is_read', 'metadata', 'created_at')
        read_only_fields = fields


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ('email_enabled', 'in_app_enabled')


class UnreadCountSerializer(serializers.Serializer):
    unread = serializers.IntegerField()


class AnnouncementSerializer(serializers.ModelSerializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all(), required=False, allow_null=True)
    author = serializers.CharField(source='created_by.get_full_name', read_only=True)
    notify = serializers.BooleanField(write_only=True, default=True, help_text='Разослать уведомления')

    class Meta:
        model = Announcement
        fields = ('id', 'org', 'course', 'title', 'content', 'author', 'notify', 'created_at')
        read_only_fields = ('id', 'org', 'author', 'created_at')


# ---------- Views ----------


@extend_schema_view(list=extend_schema(summary='Мои уведомления', parameters=[OpenApiParameter('is_read', bool),
                                                                              OpenApiParameter('type', str)]))
@extend_schema(tags=['notifications'])
class NotificationViewSet(mixins.ListModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['is_read', 'type']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Notification.objects.none()
        return Notification.objects.filter(user=self.request.user)

    @extend_schema(summary='Отметить прочитанным', request=None, responses=NotificationSerializer)
    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read', 'updated_at'])
        return Response(NotificationSerializer(notification).data)

    @extend_schema(summary='Прочитать все', request=None, responses=UnreadCountSerializer)
    @action(detail=False, methods=['post'], url_path='read-all')
    def read_all(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True, updated_at=timezone.now())
        return Response({'unread': 0})

    @extend_schema(summary='Количество непрочитанных', responses=UnreadCountSerializer)
    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        return Response({'unread': self.get_queryset().filter(is_read=False).count()})


@extend_schema(tags=['notifications'])
class NotificationPreferenceView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _prefs(self, user):
        return NotificationPreference.objects.get_or_create(user=user)[0]

    @extend_schema(summary='Настройки уведомлений', responses=NotificationPreferenceSerializer)
    def get(self, request):
        return Response(NotificationPreferenceSerializer(self._prefs(request.user)).data)

    @extend_schema(summary='Изменить настройки уведомлений', request=NotificationPreferenceSerializer,
                   responses=NotificationPreferenceSerializer)
    def patch(self, request):
        serializer = NotificationPreferenceSerializer(self._prefs(request.user), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(summary='Объявления организации и моих курсов', parameters=[OpenApiParameter('course', int)]),
    create=extend_schema(summary='Опубликовать объявление: для всей организации (админ) или курса (преподаватель)'),
)
@extend_schema(tags=['notifications'])
class AnnouncementViewSet(viewsets.ModelViewSet):
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['course']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Announcement.objects.none()
        user = self.request.user
        org_ids = list(user.memberships.filter(is_active=True).values_list('org_id', flat=True))
        if getattr(self.request, 'org_id', None):
            org_ids = [self.request.org_id]
        # Общие объявления своих организаций + объявления курсов, которые пользователь видит
        return Announcement.objects.select_related('created_by', 'course').filter(
            Q(course__isnull=True) | Q(course_id__in=viewable_course_ids(user)),
            org_id__in=org_ids,
        )

    def _check_can_publish(self, org_id, course):
        user = self.request.user
        if course:
            if not can_manage_course(user, course):
                raise PermissionDenied('Объявление курса публикует его преподаватель или админ.')
        elif not is_org_admin(user, org_id):
            raise PermissionDenied('Объявление для всей организации публикует администратор.')

    def perform_create(self, serializer):
        course = serializer.validated_data.get('course')
        org_id = course.org_id if course else getattr(self.request, 'org_id', None)
        if not org_id:
            raise ValidationError('Не выбрана организация: передайте заголовок X-Org-ID.')
        self._check_can_publish(org_id, course)
        notify = serializer.validated_data.pop('notify', True)
        announcement = serializer.save(org_id=org_id, created_by=self.request.user)
        if notify:
            self._notify(announcement)

    def perform_update(self, serializer):
        self._check_can_publish(serializer.instance.org_id, serializer.instance.course)
        serializer.validated_data.pop('notify', None)
        serializer.save()

    def perform_destroy(self, instance):
        self._check_can_publish(instance.org_id, instance.course)
        instance.delete()

    def _notify(self, announcement):
        from apps.accounts.models import User
        from apps.courses.access import active_student_ids
        if announcement.course:
            users = User.objects.filter(id__in=active_student_ids(announcement.course))
        else:
            users = User.objects.filter(memberships__org_id=announcement.org_id, memberships__is_active=True).distinct()
        users = users.exclude(id=announcement.created_by_id)
        NotificationService.notify(
            users, NotificationService.Type.ANNOUNCEMENT, title=announcement.title,
            message=announcement.content[:500], metadata={'announcement_id': announcement.id},
        )
