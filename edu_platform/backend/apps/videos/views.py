from drf_spectacular.utils import extend_schema
from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import VideoService


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
