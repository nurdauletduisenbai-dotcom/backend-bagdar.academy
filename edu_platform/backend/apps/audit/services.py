import logging

from .models import AuditLog

logger = logging.getLogger('edu_platform')


class AuditService:
    Action = AuditLog.Action

    @classmethod
    def log(cls, action: str, user=None, org_id=None, ip=None, request=None,
            entity=None, changes: dict | None = None):
        """Пишет запись журнала аудита. Ошибка записи не должна ломать основное действие."""
        try:
            if request is not None:
                ip = ip or request.META.get('REMOTE_ADDR')
                org_id = org_id or getattr(request, 'org_id', None)
            AuditLog.objects.create(
                action=action,
                user=user if user is not None and user.is_authenticated else None,
                org_id=org_id,
                ip_address=ip,
                request_id=getattr(request, 'request_id', '') if request is not None else '',
                entity_type=entity.__class__.__name__ if entity is not None else '',
                entity_id=entity.pk if entity is not None else None,
                changes=changes or {},
            )
        except Exception:  # noqa: BLE001
            logger.exception('Не удалось записать событие аудита %s', action)
