from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedModel
from apps.courses.models import Course


class Order(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает оплаты'
        PAID = 'paid', 'Оплачен'
        FAILED = 'failed', 'Ошибка оплаты'
        REFUNDED = 'refunded', 'Возврат средств'

    class Provider(models.TextChoices):
        KASPI = 'kaspi', 'Kaspi Pay'
        STRIPE = 'stripe', 'Stripe'
        MANUAL = 'manual', 'Ручное зачисление'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='orders')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='KZT')
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)

    provider = models.CharField(max_length=20, choices=Provider.choices, default=Provider.KASPI)
    provider_ref = models.CharField(max_length=255, unique=True, null=True, blank=True, db_index=True)
    idempotency_key = models.CharField(max_length=128, unique=True, db_index=True)

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        verbose_name = 'Заказ / Платеж'
