from django.contrib import admin
from .models import (
    Tenant, User, Product, Order, OrderItem, Category, AuditLog,
    ProductVariant, ProductImage, ProductReview, Wishlist, WishlistItem,
    Cart, CartItem, Coupon, ShippingAddress, SalesReport
)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'subdomain', 'owner_email', 'currency', 'tax_rate', 'is_active', 'created_at']
    search_fields = ['name', 'subdomain', 'owner_email']
    list_filter = ['is_active', 'currency']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'tenant', 'is_active']
    list_filter = ['role', 'tenant', 'is_active']
    search_fields = ['username', 'email']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'tenant', 'is_deleted', 'created_at']
    list_filter = ['tenant', 'is_deleted']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'stock', 'category', 'is_available', 'is_featured', 'tenant', 'is_deleted']
    list_filter = ['tenant', 'category', 'is_available', 'is_featured', 'is_deleted']
    search_fields = ['name', 'sku', 'barcode']


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['name', 'product', 'price', 'stock', 'is_available']
    list_filter = ['is_available', 'product__tenant']
    search_fields = ['name', 'sku']


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'is_primary', 'sort_order', 'created_at']
    list_filter = ['is_primary', 'product__tenant']


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'customer', 'rating', 'is_approved', 'is_verified_purchase', 'created_at']
    list_filter = ['is_approved', 'is_verified_purchase', 'rating', 'tenant']
    search_fields = ['title', 'comment']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['name', 'customer', 'is_public', 'tenant', 'created_at']
    list_filter = ['is_public', 'tenant']


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ['wishlist', 'product', 'added_at']
    list_filter = ['wishlist__tenant']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['customer', 'session_id', 'tenant', 'created_at']
    list_filter = ['tenant']


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'variant', 'quantity', 'added_at']
    list_filter = ['cart__tenant']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'usage_count', 'usage_limit', 'is_active', 'valid_from', 'valid_until']
    list_filter = ['discount_type', 'is_active', 'tenant']
    search_fields = ['code', 'description']


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ['name', 'customer', 'city', 'state', 'country', 'is_default']
    list_filter = ['country', 'state', 'tenant']
    search_fields = ['name', 'address_line_1', 'city']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'customer', 'total_price', 'status', 'payment_status', 'tenant', 'created_at']
    list_filter = ['status', 'payment_status', 'tenant', 'is_deleted']
    search_fields = ['order_number', 'customer__username']


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'variant', 'quantity', 'price_at_purchase']
    list_filter = ['order__tenant']
    search_fields = ['product__name']


@admin.register(SalesReport)
class SalesReportAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'period_type', 'period_start', 'period_end', 'total_orders', 'total_revenue']
    list_filter = ['period_type', 'tenant']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'model_name', 'object_id', 'user', 'tenant', 'ip_address', 'timestamp']
    list_filter = ['action', 'model_name', 'tenant']
    search_fields = ['model_name', 'user__username']
    readonly_fields = ['tenant', 'user', 'action', 'model_name', 'object_id', 'changes', 'ip_address', 'timestamp']
