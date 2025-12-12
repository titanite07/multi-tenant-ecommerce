import django_filters
from django.db import models
from .models import Product, Order, Category, AuditLog, ProductReview, Coupon


class ProductFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = django_filters.NumberFilter(field_name='category__id')
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    low_stock = django_filters.BooleanFilter(method='filter_low_stock')
    is_featured = django_filters.BooleanFilter()
    has_discount = django_filters.BooleanFilter(method='filter_has_discount')

    class Meta:
        model = Product
        fields = ['name', 'category', 'is_available', 'is_featured', 'min_price', 'max_price']

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__gt=0, is_available=True)
        return queryset.filter(stock=0)

    def filter_low_stock(self, queryset, name, value):
        if value:
            return queryset.filter(stock__lte=models.F('min_stock_threshold'))
        return queryset

    def filter_has_discount(self, queryset, name, value):
        if value:
            return queryset.filter(compare_at_price__gt=models.F('price'))
        return queryset


class OrderFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(lookup_expr='exact')
    payment_status = django_filters.CharFilter(lookup_expr='exact')
    customer = django_filters.NumberFilter(field_name='customer__id')
    date_from = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    min_total = django_filters.NumberFilter(field_name='total_price', lookup_expr='gte')
    max_total = django_filters.NumberFilter(field_name='total_price', lookup_expr='lte')
    order_number = django_filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Order
        fields = ['status', 'payment_status', 'customer', 'date_from', 'date_to', 'order_number']


class CategoryFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')
    parent = django_filters.NumberFilter(field_name='parent__id')

    class Meta:
        model = Category
        fields = ['name', 'parent']


class ProductReviewFilter(django_filters.FilterSet):
    product = django_filters.NumberFilter(field_name='product__id')
    rating = django_filters.NumberFilter()
    min_rating = django_filters.NumberFilter(field_name='rating', lookup_expr='gte')
    is_approved = django_filters.BooleanFilter()
    is_verified_purchase = django_filters.BooleanFilter()

    class Meta:
        model = ProductReview
        fields = ['product', 'rating', 'is_approved', 'is_verified_purchase']


class CouponFilter(django_filters.FilterSet):
    code = django_filters.CharFilter(lookup_expr='icontains')
    discount_type = django_filters.CharFilter()
    is_active = django_filters.BooleanFilter()

    class Meta:
        model = Coupon
        fields = ['code', 'discount_type', 'is_active']


class AuditLogFilter(django_filters.FilterSet):
    action = django_filters.CharFilter(lookup_expr='exact')
    model_name = django_filters.CharFilter(lookup_expr='icontains')
    user = django_filters.NumberFilter(field_name='user__id')
    date_from = django_filters.DateFilter(field_name='timestamp', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='timestamp', lookup_expr='lte')

    class Meta:
        model = AuditLog
        fields = ['action', 'model_name', 'user']
