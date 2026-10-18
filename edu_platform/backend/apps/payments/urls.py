from django.urls import include, path
from rest_framework.routers import SimpleRouter

from .views import OrderViewSet, StripeWebhookView

router = SimpleRouter()
router.register(r'orders', OrderViewSet, basename='orders')

urlpatterns = [
    path('webhooks/stripe/', StripeWebhookView.as_view(), name='stripe_webhook'),
    path('', include(router.urls)),
]
