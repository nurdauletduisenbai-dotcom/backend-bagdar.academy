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

    provider = models.CharField(max_length=20, choices=Provider.choices, default=Provider.MANUAL)
    provider_ref = models.CharField(max_length=255, unique=True, null=True, blank=True, db_index=True)
    idempotency_key = models.CharField(max_length=128, unique=True, db_index=True)
    checkout_url = models.URLField(max_length=1000, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='confirmed_orders')

    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        verbose_name = 'Заказ / Платеж'

    def __str__(self):
        return f'#{self.id} {self.user} → {self.course} ({self.status})'
