from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TenantViewSet, ProductViewSet, OrderViewSet, CategoryViewSet,
    AuditLogViewSet, DashboardView, UserRegistrationView, LogoutView,
    ProductVariantViewSet, ProductReviewViewSet, WishlistViewSet,
    CartViewSet, CouponViewSet, ShippingAddressViewSet, SalesReportViewSet
)

router = DefaultRouter()
router.register(r'tenants', TenantViewSet, basename='tenant')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'variants', ProductVariantViewSet, basename='variant')
router.register(r'reviews', ProductReviewViewSet, basename='review')
router.register(r'orders', OrderViewSet, basename='order')
router.register(r'wishlists', WishlistViewSet, basename='wishlist')
router.register(r'cart', CartViewSet, basename='cart')
router.register(r'coupons', CouponViewSet, basename='coupon')
router.register(r'addresses', ShippingAddressViewSet, basename='address')
router.register(r'audit-logs', AuditLogViewSet, basename='audit-log')
router.register(r'reports', SalesReportViewSet, basename='report')

urlpatterns = [
    path('', include(router.urls)),
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('logout/', LogoutView.as_view(), name='user-logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]

