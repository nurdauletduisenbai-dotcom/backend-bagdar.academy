from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Video
from .services import VideoService


class VideoPlayView(APIView):
    """
    Защищенный шлюз доступа к видеоплееру.
    Проверяет активную запись ученика или признак free_preview.
    Возвращает защищенный embed-URL без раскрытия исходных ссылок в списках.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, video_id):
        video = Video.objects.select_related('lesson__section__course').get(id=video_id)
        player_data = VideoService.get_secure_player_data(video, request.user)
        return Response(player_data)


class VideoProgressView(APIView):
    """
    Обновление прогресса просмотра видео.
    При достижении 90% просмотра автоматически помечает видео завершенным.
    """
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request, video_id):
        watched_seconds = int(request.data.get('watched_seconds', 0))
        video = Video.objects.select_related('lesson__section__course').get(id=video_id)
        res = VideoService.update_progress(video, request.user, watched_seconds)
        return Response(res, status=status.HTTP_200_OK)
