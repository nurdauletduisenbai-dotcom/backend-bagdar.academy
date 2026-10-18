import logging

from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.courses.access import is_org_admin
from apps.courses.models import Course

from .models import Order
from .providers import PROVIDERS
from .services import PaymentService

logger = logging.getLogger('edu_platform')


class OrderSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source='course.title', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'course', 'course_title', 'user', 'user_email', 'amount', 'currency', 'status', 'provider',
                  'checkout_url', 'paid_at', 'refunded_at', 'failure_reason', 'created_at')
        read_only_fields = fields


class CreateOrderSerializer(serializers.Serializer):
    course_id = serializers.IntegerField()
    provider = serializers.ChoiceField(choices=Order.Provider.choices, default=Order.Provider.MANUAL)


class PaymentProviderSerializer(serializers.Serializer):
    name = serializers.CharField()
    is_configured = serializers.BooleanField()


@extend_schema_view(list=extend_schema(
    summary='Заказы: свои (ученик/родитель) или всей организации (админ)',
    parameters=[OpenApiParameter('status', str), OpenApiParameter('course', int)],
))
@extend_schema(tags=['payments'])
class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['status', 'course', 'provider']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Order.objects.none()
        user = self.request.user
        admin_orgs = user.memberships.filter(is_active=True, role='admin').values_list('org_id', flat=True)
        qs = Order.objects.select_related('course', 'user').filter(Q(user=user) | Q(course__org_id__in=admin_orgs))
        if getattr(self.request, 'org_id', None):
            qs = qs.filter(course__org_id=self.request.org_id)
        return qs

    def _admin_order(self):
        order = self.get_object()
        if not is_org_admin(self.request.user, order.course.org_id):
            raise PermissionDenied('Действие доступно администратору организации.')
        return order

    @extend_schema(
        summary='Купить курс: создать заказ',
        description=(
            'Бесплатный курс зачисляется сразу (status=paid). Для stripe в ответе checkout_url — перенаправьте '
            'пользователя туда. Для manual заказ ждёт подтверждения администратором. '
            'Заголовок Idempotency-Key защищает от двойных заказов при повторной отправке.'
        ),
        parameters=[OpenApiParameter('Idempotency-Key', str, OpenApiParameter.HEADER, required=False)],
        request=CreateOrderSerializer,
        responses={201: OrderSerializer},
    )
    def create(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = get_object_or_404(Course, id=serializer.validated_data['course_id'])
        order = PaymentService.create_order(
            request.user, course, serializer.validated_data['provider'],
            idempotency_key=request.headers.get('Idempotency-Key'),
        )
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @extend_schema(summary='Подтвердить оплату вручную (админ, наличные/перевод)', request=None,
                   responses=OrderSerializer)
    @action(detail=True, methods=['post'], url_path='mark-paid')
    def mark_paid(self, request, pk=None):
        order = PaymentService.mark_paid(self._admin_order(), confirmed_by=request.user)
        return Response(OrderSerializer(order).data)

    @extend_schema(summary='Возврат оплаты и закрытие доступа (админ)', request=None, responses=OrderSerializer)
    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        order = PaymentService.refund(self._admin_order(), request.user)
        return Response(OrderSerializer(order).data)

    @extend_schema(summary='Отменить неоплаченный заказ', request=None, responses=OrderSerializer)
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        if order.user_id != request.user.id and not is_org_admin(request.user, order.course.org_id):
            raise PermissionDenied('Отменить можно только свой заказ.')
        return Response(OrderSerializer(PaymentService.cancel(order)).data)

    @extend_schema(summary='Доступные способы оплаты', responses=PaymentProviderSerializer(many=True))
    @action(detail=False, methods=['get'])
    def providers(self, request):
        return Response([{'name': p.name, 'is_configured': p.is_configured()} for p in PROVIDERS.values()])


@extend_schema(tags=['payments'])
class StripeWebhookView(APIView):
    """Вебхук Stripe: подпись проверяется по STRIPE_WEBHOOK_SECRET."""
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    @extend_schema(summary='Вебхук Stripe (вызывает Stripe, не клиент)', request=None, responses={200: None})
    def post(self, request):
        provider = PROVIDERS['stripe']
        if not provider.is_configured():
            return HttpResponse(status=404)
        try:
            event = provider.parse_webhook(request.body, request.headers.get('Stripe-Signature', ''))
        except Exception:  # noqa: BLE001 — неверная подпись или тело
            logger.warning('Stripe webhook: неверная подпись')
            return HttpResponse(status=400)
        result = PaymentService.handle_stripe_event(event)
        return Response({'result': result})
