from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.common.viewsets import CourseScopedViewSet
from apps.content.models import Lesson

from .models import Video
from .services import VideoService


class VideoManageSerializer(serializers.ModelSerializer):
    lesson = serializers.PrimaryKeyRelatedField(queryset=Lesson.objects.all())
    youtube_url = serializers.CharField(write_only=True, required=False,
                                        help_text='Ссылка youtube.com/watch?v=..., youtu.be/... или ID из 11 символов')
    youtube_video_id = serializers.SerializerMethodField(help_text='Виден только тем, кто управляет курсом')

    class Meta:
        model = Video
        fields = ('id', 'lesson', 'title', 'youtube_url', 'youtube_video_id', 'duration_seconds', 'order',
                  'created_at')
        read_only_fields = ('id', 'created_at')

    def get_youtube_video_id(self, obj) -> str | None:
        # ID YouTube раскрывается только тем, кто управляет курсом этого видео
        if obj.lesson.section.course_id in self.context.get('managed_course_ids', set()):
            return obj.youtube_video_id
        return None

    def validate(self, attrs):
        url = attrs.pop('youtube_url', None)
        if url:
            attrs['youtube_video_id'] = VideoService.extract_youtube_id(url)
        elif not self.instance:
            raise serializers.ValidationError({'youtube_url': 'Укажите ссылку на видео YouTube.'})
        return attrs


@extend_schema_view(
    list=extend_schema(summary='Видео уроков', parameters=[OpenApiParameter('lesson', int)]),
    create=extend_schema(summary='Добавить видео YouTube к уроку (преподаватель курса)'),
)
@extend_schema(tags=['videos'])
class VideoViewSet(CourseScopedViewSet):
    queryset = Video.objects.select_related('lesson__section__course').order_by('order', 'id')
    serializer_class = VideoManageSerializer
    course_path = 'lesson__section__course'
    filterset_fields = ['lesson']
    pagination_class = None

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        if self.request and self.request.user.is_authenticated:
            ctx['managed_course_ids'] = self.managed_ids()
        return ctx

    def course_from_data(self, validated_data):
        return validated_data['lesson'].section.course


class VideoPlayerSerializer(serializers.Serializer):
    video_id = serializers.IntegerField()
    title = serializers.CharField()
    duration_seconds = serializers.IntegerField()
    embed_url = serializers.URLField(help_text='Embed youtube-nocookie.com — вставлять в <iframe>')
    watched_seconds = serializers.IntegerField()
    is_completed = serializers.BooleanField()


class VideoProgressRequestSerializer(serializers.Serializer):
    watched_seconds = serializers.IntegerField(min_value=0)


class VideoProgressResponseSerializer(serializers.Serializer):
    watched_seconds = serializers.IntegerField()
    is_completed = serializers.BooleanField()
    progress_percent = serializers.FloatField()


@extend_schema(tags=['videos'])
class VideoPlayView(APIView):
    """
    Защищённый шлюз к видеоплееру: проверяет запись на курс или free preview
    и только тогда отдаёт embed-URL (в списках уроков ID YouTube не раскрывается).
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Получить плеер видео', responses={200: VideoPlayerSerializer})
    def get(self, request, video_id):
        video = VideoService.get_video(video_id)
        return Response(VideoService.get_secure_player_data(video, request.user))


@extend_schema(tags=['videos'])
class VideoProgressView(APIView):
    """Обновление прогресса просмотра. С 90% видео помечается просмотренным."""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(summary='Обновить прогресс просмотра', request=VideoProgressRequestSerializer,
                   responses={200: VideoProgressResponseSerializer})
    def put(self, request, video_id):
        serializer = VideoProgressRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        video = VideoService.get_video(video_id)
        result = VideoService.update_progress(video, request.user, serializer.validated_data['watched_seconds'])
        return Response(result, status=status.HTTP_200_OK)
