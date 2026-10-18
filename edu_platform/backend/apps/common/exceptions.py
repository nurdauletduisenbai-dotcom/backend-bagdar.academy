from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        code = getattr(exc, 'default_code', 'error')
        if hasattr(exc, 'get_codes'):
            try:
                code_data = exc.get_codes()
                if isinstance(code_data, str):
                    code = code_data
                elif isinstance(code_data, dict) and 'detail' in code_data:
                    code = code_data['detail']
            except Exception:
                pass

        message = 'Ошибка выполнения запроса'
        details = {}

        if isinstance(response.data, dict):
            if 'detail' in response.data:
                message = str(response.data['detail'])
                details = {k: v for k, v in response.data.items() if k != 'detail'}
            else:
                details = response.data
                message = 'Проверьте корректность переданных полей.'
        elif isinstance(response.data, list):
            details = {'non_field_errors': response.data}
            message = str(response.data[0]) if response.data else 'Ошибка валидации списка'

        custom_data = {
            'error': {
                'code': str(code).lower(),
                'message': message,
                'details': details,
            }
        }
        response.data = custom_data

    return response
