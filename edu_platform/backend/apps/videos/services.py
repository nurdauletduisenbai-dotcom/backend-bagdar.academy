import re

from django.utils import timezone
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from apps.common.permissions import STAFF_ROLES
from apps.courses.models import Enrollment

from .models import Video, VideoProgress

COMPLETION_THRESHOLD_PCT = 90
# Насколько прогресс может опережать реальное время между запросами (перемотка x2 + запас)
MAX_SPEEDUP = 2.0
SLACK_SECONDS = 15


class VideoService:
    YOUTUBE_REGEX = re.compile(
        r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|v\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    )

    @classmethod
    def extract_youtube_id(cls, raw_url_or_id: str) -> str:
        if not raw_url_or_id:
            raise ValidationError('Ссылка на видео обязательна.')

        raw = raw_url_or_id.strip()
        if re.match(r'^[a-zA-Z0-9_-]{11}$', raw):
            return raw

        match = cls.YOUTUBE_REGEX.search(raw)
        if match:
            return match.group(1)

        raise ValidationError(
            'Некорректная ссылка на видео YouTube. Ожидается формат youtube.com/watch?v=... или youtu.be/...'
        )

    @classmethod
    def get_video(cls, video_id: int) -> Video:
        video = (
            Video.objects.select_related('lesson__section__course')
            .filter(id=video_id, lesson__deleted_at__isnull=True, lesson__section__course__deleted_at__isnull=True)
            .first()
        )
        if not video:
            raise NotFound('Видео не найдено.')
        return video

    @classmethod
    def is_staff_for_video(cls, video: Video, user) -> bool:
        course = video.lesson.section.course
        return any(r in STAFF_ROLES for r in user.get_roles_for_org(course.org_id))

    @classmethod
    def verify_student_access_to_video(cls, video: Video, user) -> bool:
        """
        Персонал организации курса -> да.
        Урок опубликован и помечен is_free_preview (и превью включено в курсе) -> да.
        Ученик с активной записью на курс и опубликованный урок -> да.
        Иначе -> 403.
        """
        if cls.is_staff_for_video(video, user):
            return True

        lesson = video.lesson
        course = lesson.section.course
        if not lesson.is_published:
            raise PermissionDenied('Урок ещё не опубликован.')

        if lesson.is_free_preview and course.is_free_preview_enabled:
            return True

        is_enrolled = Enrollment.objects.filter(
            student=user,
            course=course,
            status=Enrollment.Status.ACTIVE,
            access_until__gte=timezone.now(),
        ).exists()
        if not is_enrolled:
            raise PermissionDenied('Доступ к видео закрыт: требуется активная запись на курс.')
        return True

    @classmethod
    def get_secure_player_data(cls, video: Video, user) -> dict:
        cls.verify_student_access_to_video(video, user)

        embed_url = (
            f"https://www.youtube-nocookie.com/embed/{video.youtube_video_id}"
            f"?rel=0&modestbranding=1&playsinline=1"
        )

        # Запись прогресса создаётся при открытии плеера — от неё считается реальное время просмотра
        progress, _ = VideoProgress.objects.get_or_create(video=video, student=user)
        progress.save(update_fields=['last_watched_at'])

        return {
            'video_id': video.id,
            'title': video.title,
            'duration_seconds': video.duration_seconds,
            'embed_url': embed_url,
            'watched_seconds': progress.watched_seconds,
            'is_completed': progress.is_completed,
        }

    @classmethod
    def update_progress(cls, video: Video, user, watched_seconds: int) -> dict:
        cls.verify_student_access_to_video(video, user)

        progress, created = VideoProgress.objects.get_or_create(video=video, student=user)
        now = timezone.now()

        # Нельзя «досмотреть» быстрее реального времени: прирост ограничен прошедшим временем
        elapsed = 0 if created else (now - progress.last_watched_at).total_seconds()
        max_allowed = progress.watched_seconds + int(elapsed * MAX_SPEEDUP) + SLACK_SECONDS
        if video.duration_seconds > 0:
            max_allowed = min(max_allowed, video.duration_seconds)
        progress.watched_seconds = max(progress.watched_seconds, min(watched_seconds, max_allowed))

        if video.duration_seconds > 0:
            pct = progress.watched_seconds / video.duration_seconds * 100
            if pct >= COMPLETION_THRESHOLD_PCT:
                progress.is_completed = True
        elif progress.watched_seconds > 60:
            progress.is_completed = True

        progress.save()
        return {
            'watched_seconds': progress.watched_seconds,
            'is_completed': progress.is_completed,
            'progress_percent': round(progress.watched_seconds / max(1, video.duration_seconds) * 100, 1),
        }
