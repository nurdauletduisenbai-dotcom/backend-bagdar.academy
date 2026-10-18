import logging
import uuid

logger = logging.getLogger('edu_platform')


class RequestIDMiddleware:
    """Генерирует или пробрасывает уникальный X-Request-ID для трейсинга запросов"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get('X-Request-ID') or str(uuid.uuid4())
        request.request_id = request_id

        response = self.get_response(request)
        response['X-Request-ID'] = request_id
        return response


class OrgTenantIsolationMiddleware:
    """
    Определяет текущую организацию из заголовка X-Org-ID или токена пользователя.
    Изолирует данные между разными учебными центрами и школами.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        org_id = request.headers.get('X-Org-ID')
        user = getattr(request, 'user', None)

        if not org_id and user and user.is_authenticated:
            org_id = getattr(user, 'current_org_id', None)

        request.org_id = int(org_id) if org_id and str(org_id).isdigit() else None
        return self.get_response(request)
