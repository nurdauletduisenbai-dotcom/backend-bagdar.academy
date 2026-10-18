from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import filters

from apps.common.org_viewsets import OrgScopedViewSet

from .models import Question, Topic
from .serializers import QuestionSerializer, TopicSerializer


@extend_schema_view(
    list=extend_schema(summary='Темы банка вопросов текущей организации'),
    create=extend_schema(summary='Создать тему (учитель/админ)'),
)
@extend_schema(tags=['questions'])
class TopicViewSet(OrgScopedViewSet):
    queryset = Topic.objects.order_by('subject', 'name')
    serializer_class = TopicSerializer
    filterset_fields = ['subject', 'parent']
    search_fields = ['name', 'subject']
    pagination_class = None

    def perform_create(self, serializer):
        serializer.save(org_id=self.require_org())


@extend_schema_view(
    list=extend_schema(summary='Банк вопросов (с правильными ответами — только для персонала)'),
    create=extend_schema(summary='Создать вопрос с вариантами ответов'),
    update=extend_schema(summary='Изменить вопрос (варианты заменяются переданным списком)'),
    destroy=extend_schema(summary='Удалить вопрос (если он уже в тестах — архивируется)'),
)
@extend_schema(tags=['questions'])
class QuestionViewSet(OrgScopedViewSet):
    queryset = Question.objects.select_related('topic').prefetch_related('options').order_by('-created_at')
    serializer_class = QuestionSerializer
    org_path = 'topic__org'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['topic', 'type', 'difficulty', 'is_archived']
    search_fields = ['text']
    ordering_fields = ['created_at', 'difficulty']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def perform_destroy(self, instance):
        # Вопрос, использованный в тестах, нельзя удалить без потери истории попыток
        if instance.in_tests.exists():
            instance.is_archived = True
            instance.save(update_fields=['is_archived', 'updated_at'])
        else:
            instance.delete()
