from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from apps.common.files import protected_file_response
from apps.common.viewsets import CourseScopedViewSet
from apps.courses.access import can_manage_course, can_view_course_content, has_active_enrollment, is_org_staff
from apps.courses.models import Course
from apps.notifications.services import NotificationService
from apps.progress.services import ProgressService

from .models import Comment, Lesson, Material, Section
from .serializers import (
    CommentSerializer,
    LessonDetailSerializer,
    LessonSerializer,
    MaterialSerializer,
    SectionSerializer,
)


def _published_q(prefix=''):
    now = timezone.now()
    return Q(**{f'{prefix}publish_at__isnull': True}) | Q(**{f'{prefix}publish_at__lte': now})


@extend_schema_view(
    list=extend_schema(summary='Разделы курса', parameters=[OpenApiParameter('course', int, required=False)]),
    create=extend_schema(summary='Создать раздел (преподаватель курса)'),
)
@extend_schema(tags=['content'])
class SectionViewSet(CourseScopedViewSet):
    queryset = Section.objects.select_related('course').order_by('course_id', 'order', 'id')
    serializer_class = SectionSerializer
    filterset_fields = ['course']
    pagination_class = None


@extend_schema_view(
    list=extend_schema(summary='Уроки', parameters=[OpenApiParameter('section', int), OpenApiParameter('course', int)]),
    retrieve=extend_schema(summary='Урок: видео, материалы, задания, тесты', responses=LessonDetailSerializer),
)
@extend_schema(tags=['content'])
class LessonViewSet(CourseScopedViewSet):
    queryset = Lesson.objects.select_related('section__course').order_by('section__order', 'order', 'id')
    serializer_class = LessonSerializer
    course_path = 'section__course'
    filterset_fields = ['section']
    pagination_class = None

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Lesson.objects.none()
        qs = super().get_queryset()
        course_id = self.request.query_params.get('course')
        if course_id and course_id.isdigit():
            qs = qs.filter(section__course_id=course_id)
        return qs

    def filter_for_learner(self, qs):
        # Неопубликованные уроки видит только тот, кто управляет курсом
        return qs.filter(Q(section__course_id__in=self.managed_ids()) | _published_q())

    def get_object(self):
        # Бесплатный превью-урок опубликованного курса доступен любому авторизованному
        lookup = self.kwargs[self.lookup_field]
        lesson = self.get_queryset().filter(pk=lookup).first()
        if lesson is None and self.action == 'retrieve':
            lesson = get_object_or_404(
                Lesson.objects.select_related('section__course').filter(_published_q()),
                pk=lookup,
                is_free_preview=True,
                section__course__status=Course.Status.PUBLISHED,
                section__course__is_free_preview_enabled=True,
            )
        if lesson is None:
            lesson = get_object_or_404(Lesson.objects.none(), pk=lookup)
        self.check_object_permissions(self.request, lesson)
        return lesson

    def course_from_data(self, validated_data):
        return validated_data['section'].course

    def retrieve(self, request, *args, **kwargs):
        lesson = self.get_object()
        has_access = can_view_course_content(request.user, lesson.section.course)
        data = LessonDetailSerializer(lesson, context={'request': request, 'has_access': has_access}).data
        return Response(data)

    @extend_schema(summary='Отметить урок пройденным (ученик)', request=None,
                   responses={200: {'type': 'object', 'properties': {'is_completed': {'type': 'boolean'}}}})
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        lesson = self.get_object()
        if not has_active_enrollment(request.user, lesson.section.course):
            raise PermissionDenied('Отмечать уроки могут только записанные на курс ученики.')
        ProgressService.mark_lesson_completed(request.user, lesson)
        return Response({'is_completed': True})


@extend_schema_view(
    list=extend_schema(summary='Материалы урока', parameters=[OpenApiParameter('lesson', int)]),
    create=extend_schema(summary='Добавить материал: файл (multipart) или ссылка'),
)
@extend_schema(tags=['content'])
class MaterialViewSet(CourseScopedViewSet):
    queryset = Material.objects.select_related('lesson__section__course').order_by('order', 'id')
    serializer_class = MaterialSerializer
    course_path = 'lesson__section__course'
    filterset_fields = ['lesson']
    pagination_class = None
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def course_from_data(self, validated_data):
        return validated_data['lesson'].section.course

    @extend_schema(summary='Скачать файл материала', responses={(200, 'application/octet-stream'): bytes})
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        material = self.get_object()
        return protected_file_response(material.file, material.title)


@extend_schema_view(
    list=extend_schema(summary='Комментарии и вопросы к уроку', parameters=[OpenApiParameter('lesson', int)]),
    create=extend_schema(summary='Написать комментарий или ответить (parent)'),
    destroy=extend_schema(summary='Удалить свой комментарий (или любой — персонал)'),
)
@extend_schema(tags=['content'])
class CommentViewSet(CourseScopedViewSet):
    queryset = Comment.objects.select_related('user', 'lesson__section__course').order_by('created_at')
    serializer_class = CommentSerializer
    course_path = 'lesson__section__course'
    filterset_fields = ['lesson', 'parent']

    def filter_for_learner(self, qs):
        return qs.filter(Q(is_hidden=False) | Q(user=self.request.user) | Q(lesson__section__course_id__in=self.managed_ids()))

    def course_from_data(self, validated_data):
        return validated_data['lesson'].section.course

    def _is_moderator(self, comment):
        course = comment.lesson.section.course
        return can_manage_course(self.request.user, course) or is_org_staff(self.request.user, course.org_id)

    def perform_create(self, serializer):
        course = self.course_from_data(serializer.validated_data)
        if not can_view_course_content(self.request.user, course):
            raise PermissionDenied('Комментировать могут ученики курса и его преподаватели.')
        comment = serializer.save(user=self.request.user)
        parent = comment.parent
        if parent and parent.user_id != self.request.user.id:
            NotificationService.notify(
                [parent.user], NotificationService.Type.COMMENT_REPLY,
                title='Ответ на ваш комментарий',
                message=f'{self.request.user.get_full_name()}: {comment.content[:200]}',
                metadata={'lesson_id': comment.lesson_id, 'comment_id': comment.id},
            )

    def perform_update(self, serializer):
        if serializer.instance.user_id != self.request.user.id:
            raise PermissionDenied('Редактировать можно только свой комментарий.')
        serializer.save()

    def perform_destroy(self, instance):
        if instance.user_id != self.request.user.id and not self._is_moderator(instance):
            raise PermissionDenied('Удалить можно только свой комментарий.')
        instance.delete()

    @extend_schema(summary='Скрыть/показать комментарий (персонал)', request=None, responses=CommentSerializer)
    @action(detail=True, methods=['post'], url_path='toggle-hidden')
    def toggle_hidden(self, request, pk=None):
        comment = self.get_object()
        if not self._is_moderator(comment):
            raise PermissionDenied('Скрывать комментарии может только персонал.')
        comment.is_hidden = not comment.is_hidden
        comment.save(update_fields=['is_hidden', 'updated_at'])
        return Response(CommentSerializer(comment, context={'request': request}).data, status=status.HTTP_200_OK)
