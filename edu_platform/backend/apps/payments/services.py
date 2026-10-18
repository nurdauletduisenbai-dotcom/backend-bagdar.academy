import uuid
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.audit.services import AuditService
from apps.courses.access import has_active_enrollment
from apps.courses.models import Course, Enrollment
from apps.notifications.services import NotificationService

from .models import Order
from .providers import get_provider


class PaymentService:
    @classmethod
    def ensure_enabled(cls):
        if not settings.FEATURE_PAYMENTS_ENABLED:
            raise ValidationError('Онлайн-оплата отключена.')

    @classmethod
    def create_order(cls, user, course: Course, provider: str, idempotency_key: str | None = None) -> Order:
        cls.ensure_enabled()
        if idempotency_key:
            existing = Order.objects.filter(idempotency_key=idempotency_key).first()
            if existing:
                if existing.user_id != user.id:
                    raise ValidationError('Этот ключ идемпотентности уже использован.')
                return existing

        if course.status != Course.Status.PUBLISHED:
            raise ValidationError({'course_id': 'Курс недоступен для покупки.'})
        if not user.memberships.filter(org_id=course.org_id, is_active=True).exists():
            raise ValidationError({'course_id': 'Курс другой организации.'})
        if has_active_enrollment(user, course):
            raise ValidationError({'course_id': 'Вы уже записаны на этот курс.'})

        # Бесплатный курс — сразу зачисляем
        if course.price <= 0:
            order = Order.objects.create(
                user=user, course=course, amount=0, provider=Order.Provider.MANUAL,
                idempotency_key=idempotency_key or uuid.uuid4().hex,
            )
            return cls.mark_paid(order)

        pending = Order.objects.filter(user=user, course=course, provider=provider, status=Order.Status.PENDING).first()
        if pending:
            return pending

        gateway = get_provider(provider)
        try:
            with transaction.atomic():
                order = Order.objects.create(
                    user=user, course=course, amount=course.price, provider=provider,
                    idempotency_key=idempotency_key or uuid.uuid4().hex,
                )
                checkout = gateway.create_checkout(order)
                order.checkout_url = checkout.get('checkout_url') or ''
                order.provider_ref = checkout.get('provider_ref')
                order.save(update_fields=['checkout_url', 'provider_ref', 'updated_at'])
        except IntegrityError as exc:
            raise ValidationError('Заказ с таким ключом уже существует.') from exc
        return order

    @classmethod
    @transaction.atomic
    def mark_paid(cls, order: Order, confirmed_by=None, provider_ref: str | None = None) -> Order:
        """Идемпотентно: повторный вебхук или повторное подтверждение ничего не ломают."""
        order = Order.objects.select_for_update().select_related('course', 'user').get(pk=order.pk)
        if order.status == Order.Status.PAID:
            return order
        if order.status == Order.Status.REFUNDED:
            raise ValidationError('Заказ уже возвращён.')

        order.status = Order.Status.PAID
        order.paid_at = timezone.now()
        order.confirmed_by = confirmed_by
        if provider_ref and not order.provider_ref:
            order.provider_ref = provider_ref
        order.save()

        enrollment, created = Enrollment.objects.get_or_create(
            course=order.course, student=order.user,
            defaults={'status': Enrollment.Status.ACTIVE,
                      'access_until': timezone.now() + timedelta(days=order.course.access_days)},
        )
        if not created:
            base = max(enrollment.access_until, timezone.now()) if enrollment.is_current_active else timezone.now()
            enrollment.status = Enrollment.Status.ACTIVE
            enrollment.access_until = base + timedelta(days=order.course.access_days)
            enrollment.save(update_fields=['status', 'access_until', 'updated_at'])

        NotificationService.notify(
            [order.user], NotificationService.Type.ENROLLMENT,
            title=f'Доступ к курсу «{order.course.title}» открыт',
            message=f'Доступ до {timezone.localtime(enrollment.access_until):%d.%m.%Y}.',
            metadata={'order_id': order.id, 'course_id': order.course_id},
            email=True,
        )
        AuditService.log(AuditService.Action.PAYMENT_PAID, user=confirmed_by or order.user, org_id=order.course.org_id,
                         entity=order, changes={'amount': str(order.amount), 'provider': order.provider})
        return order

    @classmethod
    @transaction.atomic
    def refund(cls, order: Order, by_user) -> Order:
        order = Order.objects.select_for_update().select_related('course', 'user').get(pk=order.pk)
        if order.status != Order.Status.PAID:
            raise ValidationError('Вернуть можно только оплаченный заказ.')
        if order.amount > 0:
            get_provider(order.provider).refund(order)

        order.status = Order.Status.REFUNDED
        order.refunded_at = timezone.now()
        order.save(update_fields=['status', 'refunded_at', 'updated_at'])
        Enrollment.objects.filter(course=order.course, student=order.user).update(
            status=Enrollment.Status.CANCELED, updated_at=timezone.now()
        )
        NotificationService.notify(
            [order.user], NotificationService.Type.PAYMENT,
            title=f'Возврат по курсу «{order.course.title}»',
            message='Оплата возвращена, доступ к курсу закрыт.',
            metadata={'order_id': order.id},
            email=True,
        )
        AuditService.log(AuditService.Action.PAYMENT_REFUND, user=by_user, org_id=order.course.org_id, entity=order)
        return order

    @classmethod
    def cancel(cls, order: Order) -> Order:
        if order.status != Order.Status.PENDING:
            raise ValidationError('Отменить можно только неоплаченный заказ.')
        order.status = Order.Status.FAILED
        order.failure_reason = 'Отменён пользователем'
        order.save(update_fields=['status', 'failure_reason', 'updated_at'])
        return order

    @classmethod
    def handle_stripe_event(cls, event) -> str:
        data = event['data']['object']
        order_id = (data.get('metadata') or {}).get('order_id') or data.get('client_reference_id')
        order = Order.objects.filter(id=order_id, provider=Order.Provider.STRIPE).first() if order_id else None
        if order is None:
            return 'ignored'
        if event['type'] == 'checkout.session.completed' and data.get('payment_status') == 'paid':
            cls.mark_paid(order, provider_ref=data.get('id'))
            return 'paid'
        if event['type'] in ('checkout.session.expired', 'checkout.session.async_payment_failed'):
            if order.status == Order.Status.PENDING:
                order.status = Order.Status.FAILED
                order.failure_reason = event['type']
                order.save(update_fields=['status', 'failure_reason', 'updated_at'])
            return 'failed'
        return 'ignored'
