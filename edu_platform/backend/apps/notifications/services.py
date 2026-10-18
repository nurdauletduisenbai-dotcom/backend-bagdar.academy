from collections.abc import Iterable

from django.db import transaction

from .models import Notification, NotificationPreference


class NotificationService:
    Type = Notification.Type

    @classmethod
    def notify(cls, users: Iterable, type: str, title: str, message: str = '', metadata: dict | None = None,
               email: bool = False) -> int:
        """
        Создаёт in-app уведомления (с учётом настроек пользователя) и при email=True
        ставит отправку писем в очередь Celery после коммита транзакции.
        Возвращает число созданных уведомлений.
        """
        users = [u for u in users if u is not None]
        if not users:
            return 0
        user_ids = {u.id if hasattr(u, 'id') else int(u) for u in users}
        prefs = {p.user_id: p for p in NotificationPreference.objects.filter(user_id__in=user_ids)}

        in_app, by_email = [], []
        for uid in user_ids:
            pref = prefs.get(uid)
            if pref is None or pref.in_app_enabled:
                in_app.append(Notification(user_id=uid, type=type, title=title, message=message,
                                           metadata=metadata or {}))
            if email and (pref is None or pref.email_enabled):
                by_email.append(uid)

        Notification.objects.bulk_create(in_app)

        if by_email:
            from .tasks import send_email_notification_task

            def _send():
                for uid in by_email:
                    send_email_notification_task.delay(
                        user_id=uid, subject=title, template='notification', context={'message': message}
                    )
            transaction.on_commit(_send)
        return len(in_app)

    @classmethod
    def already_sent(cls, user_id: int, type: str, **metadata) -> bool:
        """Защита от повторных напоминаний (например, о дедлайне) по ключам metadata."""
        qs = Notification.objects.filter(user_id=user_id, type=type)
        for key, value in metadata.items():
            qs = qs.filter(**{f'metadata__{key}': value})
        return qs.exists()
