import re

from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from apps.courses.models import Enrollment

from .models import Video, VideoProgress


class VideoService:
    YOUTUBE_REGEX = re.compile(
        r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|v\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    )

    @classmethod
    def extract_youtube_id(cls, raw_url_or_id: str) -> str:
        if not raw_url_or_id:
            raise ValidationError("Ссылка на видео обязательна.")

        raw = raw_url_or_id.strip()
        # Если передан сразу 11-значный ID
        if re.match(r'^[a-zA-Z0-9_-]{11}$', raw):
            return raw

        match = cls.YOUTUBE_REGEX.search(raw)
        if match:
            return match.group(1)

        raise ValidationError("Некорректная ссылка на видео YouTube. Ожидается формат youtube.com/watch?v=... или youtu.be/...")

    @classmethod
    def verify_student_access_to_video(cls, video: Video, user) -> bool:
        """
        Проверяет, имеет ли пользователь право смотреть это видео.
        Учитель/Админ -> Всегда Да
        Урок помечен is_free_preview -> Да
        Ученик с активной записью на курс -> Да
        Иначе -> 403 Forbidden!
        """
        if user.is_superuser:
            return True

        roles = user.get_roles_for_org()
        if 'admin' in roles or 'teacher' in roles or 'curator' in roles:
            return True

        if video.lesson.is_free_preview:
            return True

        course_id = video.lesson.section.course_id
        is_enrolled = Enrollment.objects.filter(
            student=user,
            course_id=course_id,
            status='active',
            access_until__gte=timezone.now()
        ).exists()

        if not is_enrolled:
            raise PermissionDenied("Доступ к видео закрыт: требуется активная запись на курс.")

        return True

    @classmethod
    def get_secure_player_data(cls, video: Video, user):
        cls.verify_student_access_to_video(video, user)

        # Безопасный URL плеера без передачи исходного видео ID в открытые списки уроков
        embed_url = (
            f"https://www.youtube-nocookie.com/embed/{video.youtube_video_id}"
            f"?rel=0&modestbranding=1&playsinline=1"
        )

        progress = VideoProgress.objects.filter(video=video, student=user).first()
        watched_seconds = progress.watched_seconds if progress else 0
        is_completed = progress.is_completed if progress else False

        return {
            'video_id': video.id,
            'title': video.title,
            'duration_seconds': video.duration_seconds,
            'embed_url': embed_url,
            'watched_seconds': watched_seconds,
            'is_completed': is_completed,
        }

    @classmethod
    def update_progress(cls, video: Video, user, watched_seconds: int):
        cls.verify_student_access_to_video(video, user)

        progress, created = VideoProgress.objects.get_or_create(
            video=video,
            student=user,
            defaults={'watched_seconds': watched_seconds}
        )

        if watched_seconds > progress.watched_seconds:
            progress.watched_seconds = watched_seconds

        # Автоматическая отметка выполненным при 90% просмотра
        if video.duration_seconds > 0:
            pct = (progress.watched_seconds / video.duration_seconds) * 100
            if pct >= 90:
                progress.is_completed = True
        elif watched_seconds > 60:
            progress.is_completed = True

        progress.save()
        return {
            'watched_seconds': progress.watched_seconds,
            'is_completed': progress.is_completed,
            'progress_percent': round((progress.watched_seconds / max(1, video.duration_seconds)) * 100, 1)
        }
