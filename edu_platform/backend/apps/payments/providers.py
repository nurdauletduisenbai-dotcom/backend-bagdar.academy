"""
Платёжные провайдеры.

- manual — оплата наличными/переводом: заказ подтверждает администратор организации (mark-paid).
- stripe — Stripe Checkout (карты). Нужны STRIPE_SECRET_KEY и STRIPE_WEBHOOK_SECRET.
- kaspi  — требует договора с Kaspi и документации мерчанта; пока не подключён (вернёт 400).
"""
from decimal import Decimal

from django.conf import settings
from rest_framework.exceptions import ValidationError


class BaseProvider:
    name = ''

    def is_configured(self) -> bool:
        return True

    def create_checkout(self, order) -> dict:
        """Возвращает {'checkout_url': str, 'provider_ref': str | None}."""
        raise NotImplementedError

    def refund(self, order):
        """Возврат средств у провайдера (для manual — ничего не делаем)."""


class ManualProvider(BaseProvider):
    name = 'manual'

    def create_checkout(self, order) -> dict:
        return {'checkout_url': '', 'provider_ref': None}


class StripeProvider(BaseProvider):
    name = 'stripe'
    # Валюты без дробной части в Stripe (KZT к ним не относится)
    ZERO_DECIMAL = {'JPY', 'KRW', 'VND'}

    def is_configured(self) -> bool:
        return bool(settings.STRIPE_SECRET_KEY)

    def _client(self):
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        return stripe

    def _amount(self, order) -> int:
        multiplier = 1 if order.currency.upper() in self.ZERO_DECIMAL else 100
        return int(Decimal(order.amount) * multiplier)

    def create_checkout(self, order) -> dict:
        stripe = self._client()
        base = settings.FRONTEND_URL
        session = stripe.checkout.Session.create(
            mode='payment',
            line_items=[{
                'quantity': 1,
                'price_data': {
                    'currency': order.currency.lower(),
                    'unit_amount': self._amount(order),
                    'product_data': {'name': order.course.title},
                },
            }],
            customer_email=order.user.email,
            client_reference_id=str(order.id),
            metadata={'order_id': str(order.id)},
            success_url=f'{base}/payments/success?order={order.id}',
            cancel_url=f'{base}/payments/cancel?order={order.id}',
            idempotency_key=order.idempotency_key,
        )
        return {'checkout_url': session.url, 'provider_ref': session.id}

    def refund(self, order):
        stripe = self._client()
        session = stripe.checkout.Session.retrieve(order.provider_ref)
        if session.payment_intent:
            stripe.Refund.create(payment_intent=session.payment_intent)

    def webhook_configured(self) -> bool:
        # Без секрета подпись проверялась бы пустым ключом — её может подделать кто угодно
        return self.is_configured() and bool(settings.STRIPE_WEBHOOK_SECRET)

    def parse_webhook(self, payload: bytes, signature: str):
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise ValueError('STRIPE_WEBHOOK_SECRET не задан')
        stripe = self._client()
        return stripe.Webhook.construct_event(payload, signature, settings.STRIPE_WEBHOOK_SECRET)


class KaspiProvider(BaseProvider):
    name = 'kaspi'

    def is_configured(self) -> bool:
        return False

    def create_checkout(self, order) -> dict:
        raise ValidationError('Kaspi Pay пока не подключён: нужен договор и API мерчанта.')


PROVIDERS = {p.name: p for p in (ManualProvider(), StripeProvider(), KaspiProvider())}


def get_provider(name: str) -> BaseProvider:
    provider = PROVIDERS.get(name)
    if provider is None:
        raise ValidationError({'provider': 'Неизвестный способ оплаты.'})
    if not provider.is_configured():
        raise ValidationError({'provider': f'Способ оплаты «{name}» не настроен.'})
    return provider
