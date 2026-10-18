from rest_framework.exceptions import PermissionDenied


def resolve_org_id(user, requested_org_id=None):
    """
    Определяет текущую организацию пользователя.

    1. Явно запрошенная (заголовок X-Org-ID или org_id из JWT) — только если пользователь
       в ней состоит (суперпользователь — в любой).
    2. Иначе, если пользователь состоит ровно в одной организации — она.
    3. Иначе None: роли пустые, данные организаций недоступны.
    """
    if not user or not user.is_authenticated:
        return requested_org_id

    if requested_org_id:
        if user.is_superuser or user.memberships.filter(org_id=requested_org_id, is_active=True).exists():
            return requested_org_id
        raise PermissionDenied('Нет доступа к этой организации.')

    org_ids = set(user.memberships.filter(is_active=True).values_list('org_id', flat=True))
    if len(org_ids) == 1:
        return org_ids.pop()
    return None
