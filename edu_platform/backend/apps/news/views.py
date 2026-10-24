import mimetypes

from django.http import FileResponse
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import Post
from .serializers import ContactRequestSerializer, PlatformStatsSerializer, PostDetailSerializer, PostListSerializer


@extend_schema_view(
    list=extend_schema(summary='Новости платформы (публично)'),
    retrieve=extend_schema(summary='Публикация по slug (публично)'),
)
@extend_schema(tags=['news'])
class PostViewSet(viewsets.ReadOnlyModelViewSet):
    """Публичная лента для главной страницы: только опубликованное, без входа."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    lookup_field = 'slug'
    lookup_value_regex = '[^/]+'
    filterset_fields = ['category', 'is_pinned']
    search_fields = ['title', 'excerpt', 'body']
    ordering_fields = ['published_at']

    def get_queryset(self):
        return Post.objects.published()

    def get_serializer_class(self):
        return PostDetailSerializer if self.action == 'retrieve' else PostListSerializer

    @extend_schema(summary='Обложка публикации', responses={(200, 'image/*'): bytes})
    @action(detail=True, methods=['get'])
    def cover(self, request, slug=None):
        post = self.get_object()
        if not post.cover:
            raise NotFound('У публикации нет обложки.')
        try:
            handle = post.cover.open('rb')
        except FileNotFoundError as exc:
            raise NotFound('Файл не найден в хранилище.') from exc
        content_type = mimetypes.guess_type(post.cover.name)[0] or 'application/octet-stream'
        response = FileResponse(handle, content_type=content_type)
        response['Cache-Control'] = 'public, max-age=86400'
        return response


@extend_schema(tags=['news'])
class PlatformStatsView(APIView):
    """Цифры для главной страницы: только агрегаты, без персональных данных."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(summary='Платформа в цифрах (публично)', responses=PlatformStatsSerializer)
    def get(self, request):
        from apps.courses.models import Course
        from apps.organizations.models import Organization, OrgMembership

        members = OrgMembership.objects.filter(is_active=True, org__is_active=True)
        data = {
            'courses': Course.objects.filter(status=Course.Status.PUBLISHED, org__is_active=True).count(),
            'students': members.filter(role='student').values('user').distinct().count(),
            'teachers': members.filter(role='teacher').values('user').distinct().count(),
            'schools': Organization.objects.filter(is_active=True).count(),
        }
        return Response(PlatformStatsSerializer(data).data)


@extend_schema(tags=['news'])
class ContactRequestView(APIView):
    """Заявка с главной страницы. Без входа; не чаще THROTTLE_PUBLIC_FORM_RATE с одного IP."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'public_form'

    @extend_schema(summary='Оставить заявку (публично)', request=ContactRequestSerializer, responses={201: None})
    def post(self, request):
        serializer = ContactRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)
