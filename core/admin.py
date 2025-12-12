from django.contrib import admin
from .models import Tenant, User, Product, Order


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'subdomain', 'owner_email', 'created_at']
    search_fields = ['name', 'subdomain', 'owner_email']


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role', 'tenant', 'is_active']
    list_filter = ['role', 'tenant', 'is_active']
    search_fields = ['username', 'email']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'stock', 'tenant', 'created_at']
    list_filter = ['tenant']
    search_fields = ['name']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'total_price', 'status', 'tenant', 'created_at']
    list_filter = ['status', 'tenant']
    search_fields = ['customer__username']
