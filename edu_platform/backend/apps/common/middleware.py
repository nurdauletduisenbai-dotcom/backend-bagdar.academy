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
    Читает запрошенную организацию из заголовка X-Org-ID в request.org_id.
    Для JWT-пользователей значение затем проверяется по членству
    в apps.common.authentication.TenantJWTAuthentication.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        org_id = request.headers.get('X-Org-ID', '')
        request.org_id = int(org_id) if org_id.isdigit() else None
        return self.get_response(request)
