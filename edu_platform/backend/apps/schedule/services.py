from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.courses.models import Enrollment
from apps.notifications.services import NotificationService

from .models import Attendance, Session


def group_student_ids(group):
    return Enrollment.objects.filter(
        group=group, status=Enrollment.Status.ACTIVE, access_until__gte=timezone.now()
    ).values_list('student_id', flat=True)


class ScheduleService:
    @classmethod
    def validate_slot(cls, group, start, end, exclude_id=None):
        if end <= start:
            raise ValidationError({'end_time': 'Окончание должно быть позже начала.'})
        overlap = Session.objects.filter(group=group, is_canceled=False, start_time__lt=end, end_time__gt=start)
        if exclude_id:
            overlap = overlap.exclude(id=exclude_id)
        if overlap.exists():
            raise ValidationError('У группы уже есть занятие в это время.')

    @classmethod
    @transaction.atomic
    def mark_attendance(cls, session: Session, records: list[dict]) -> list[Attendance]:
        allowed = set(group_student_ids(session.group))
        unknown = {r['student_id'] for r in records} - allowed
        if unknown:
            raise ValidationError({'records': f'Ученики не из этой группы: {sorted(unknown)}'})
        result = []
        for r in records:
            att, _ = Attendance.objects.update_or_create(
                session=session, student_id=r['student_id'],
                defaults={'status': r['status'], 'notes': r.get('notes', '')},
            )
            result.append(att)
        return result

    @classmethod
    def notify_canceled(cls, session: Session):
        from apps.accounts.models import User
        NotificationService.notify(
            User.objects.filter(id__in=group_student_ids(session.group)), NotificationService.Type.SYSTEM,
            title=f'Занятие отменено: {session.title}',
            message=f'{timezone.localtime(session.start_time):%d.%m.%Y %H:%M}',
            metadata={'session_id': session.id},
            email=True,
        )

    @classmethod
    def send_session_reminders(cls, minutes_before: int = 30) -> int:
        from apps.accounts.models import User
        now = timezone.now()
        sessions = Session.objects.filter(
            is_canceled=False, reminder_sent_at__isnull=True,
            start_time__gt=now, start_time__lte=now + timedelta(minutes=minutes_before),
        ).select_related('group')
        sent = 0
        for session in sessions:
            sent += NotificationService.notify(
                User.objects.filter(id__in=group_student_ids(session.group)), NotificationService.Type.SESSION_START,
                title=f'Скоро занятие: {session.title}',
                message=f'Начало в {timezone.localtime(session.start_time):%H:%M}.'
                        + (f' Ссылка: {session.online_meeting_url}' if session.online_meeting_url else ''),
                metadata={'session_id': session.id},
            )
            session.reminder_sent_at = now
            session.save(update_fields=['reminder_sent_at'])
        return sent
