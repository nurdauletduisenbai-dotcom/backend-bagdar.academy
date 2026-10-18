import mimetypes
import os
import uuid

from django.conf import settings
from django.http import FileResponse
from django.utils.deconstruct import deconstructible
from rest_framework.exceptions import NotFound, ValidationError

ALLOWED_EXTENSIONS = {
    '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx', '.txt', '.md', '.csv',
    '.png', '.jpg', '.jpeg', '.gif', '.webp', '.zip', '.py', '.ipynb',
}


def validate_upload(file):
    """Проверка размера и расширения загружаемого файла."""
    if file is None:
        return None
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if file.size > max_bytes:
        raise ValidationError({'file': f'Файл больше {settings.MAX_UPLOAD_SIZE_MB} МБ.'})
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError({'file': f'Недопустимый тип файла {ext or "(без расширения)"}.'})
    return file


@deconstructible
class UploadTo:
    """Случайное имя файла: исходное имя не раскрывает путь и не перезаписывает чужие файлы."""

    def __init__(self, prefix: str):
        self.prefix = prefix

    def __call__(self, instance, filename):
        ext = os.path.splitext(filename)[1].lower()
        return f'{self.prefix}/{uuid.uuid4().hex}{ext}'

    def __eq__(self, other):
        return isinstance(other, UploadTo) and other.prefix == self.prefix


upload_to = UploadTo


def protected_file_response(field_file, download_name: str):
    """
    Отдаёт файл только через API после проверки прав (media-каталог наружу не публикуется).
    """
    if not field_file:
        raise NotFound('Файл не прикреплён.')
    try:
        handle = field_file.open('rb')
    except FileNotFoundError as exc:
        raise NotFound('Файл не найден в хранилище.') from exc
    ext = os.path.splitext(field_file.name)[1]
    name = download_name if download_name.lower().endswith(ext) else f'{download_name}{ext}'
    content_type = mimetypes.guess_type(field_file.name)[0] or 'application/octet-stream'
    return FileResponse(handle, as_attachment=True, filename=name, content_type=content_type)
