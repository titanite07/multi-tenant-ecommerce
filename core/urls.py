from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TenantViewSet, ProductViewSet, OrderViewSet, UserRegistrationView

router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
]
