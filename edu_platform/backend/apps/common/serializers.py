from rest_framework import serializers


class MessageSerializer(serializers.Serializer):
    """Стандартный ответ с текстовым сообщением."""
    message = serializers.CharField()


class ErrorBodySerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField()


class ErrorSerializer(serializers.Serializer):
    """Формат всех ошибок API (apps.common.exceptions.custom_exception_handler)."""
    error = ErrorBodySerializer()
