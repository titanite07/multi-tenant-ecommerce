from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db import transaction
from .models import (
    Tenant, User, Product, Order, OrderItem, Category, AuditLog,
    ProductVariant, ProductImage, ProductReview, Wishlist, WishlistItem,
    Cart, CartItem, Coupon, ShippingAddress, SalesReport
)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['tenant_id'] = user.tenant.id if user.tenant else None
        token['role'] = user.role
        token['username'] = user.username
        return token


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'subdomain', 'owner_email', 'is_active', 'logo_url', 'currency', 'tax_rate', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    tenant_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'tenant', 'tenant_id', 'phone', 'address']
        read_only_fields = ['id', 'tenant']

    def create(self, validated_data):
        tenant_id = validated_data.pop('tenant_id', None)
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        if tenant_id:
            user.tenant_id = tenant_id
        user.save()
        return user


class CategorySerializer(serializers.ModelSerializer):
    subcategories = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'image_url', 'parent', 'subcategories', 'product_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_subcategories(self, obj):
        return CategorySerializer(obj.subcategories.filter(is_deleted=False), many=True).data

    def get_product_count(self, obj):
        return obj.products.filter(is_deleted=False).count()


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ['id', 'name', 'sku', 'price', 'stock', 'attributes', 'image_url', 'is_available', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image_url', 'alt_text', 'is_primary', 'sort_order', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProductReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.username', read_only=True)

    class Meta:
        model = ProductReview
        fields = ['id', 'product', 'customer', 'customer_name', 'rating', 'title', 'comment', 'is_approved', 'is_verified_purchase', 'created_at']
        read_only_fields = ['id', 'customer', 'is_approved', 'is_verified_purchase', 'created_at']


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_low_stock = serializers.BooleanField(read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    discount_percentage = serializers.FloatField(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'compare_at_price', 'cost_price', 'stock',
            'category', 'category_name', 'sku', 'barcode', 'weight', 'is_available', 'is_featured',
            'min_stock_threshold', 'image_url', 'is_low_stock', 'is_in_stock', 'discount_percentage',
            'average_rating', 'review_count', 'variants', 'images', 'tenant', 'is_deleted', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'is_deleted', 'created_at', 'updated_at']

    def get_review_count(self, obj):
        return obj.reviews.filter(is_approved=True).count()


class WishlistItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    product_image = serializers.URLField(source='product.image_url', read_only=True)

    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'product_name', 'product_price', 'product_image', 'added_at']
        read_only_fields = ['id', 'added_at']


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()

    class Meta:
        model = Wishlist
        fields = ['id', 'name', 'is_public', 'items', 'item_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_item_count(self, obj):
        return obj.items.count()


class CartItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_price = serializers.DecimalField(source='product.price', max_digits=10, decimal_places=2, read_only=True)
    product_image = serializers.URLField(source='product.image_url', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True, allow_null=True)

    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_name', 'product_price', 'product_image', 'variant', 'variant_name', 'quantity', 'subtotal', 'added_at']
        read_only_fields = ['id', 'added_at']


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    item_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Cart
        fields = ['id', 'customer', 'session_id', 'items', 'total', 'item_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'customer', 'created_at', 'updated_at']


class CouponSerializer(serializers.ModelSerializer):
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'description', 'discount_type', 'discount_value', 'minimum_purchase',
            'maximum_discount', 'usage_limit', 'usage_count', 'is_active', 'is_valid',
            'valid_from', 'valid_until', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'usage_count', 'created_at', 'updated_at']


class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = [
            'id', 'name', 'phone', 'address_line_1', 'address_line_2', 'city', 'state',
            'postal_code', 'country', 'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True, allow_null=True)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'variant', 'variant_name', 'quantity', 'price_at_purchase', 'subtotal', 'created_at']
        read_only_fields = ['id', 'price_at_purchase', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.username', read_only=True)
    item_count = serializers.SerializerMethodField()
    coupon_code = serializers.CharField(source='coupon.code', read_only=True, allow_null=True)

    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer', 'customer_name', 'items', 'item_count',
            'subtotal', 'discount_amount', 'tax_amount', 'shipping_amount', 'total_price',
            'status', 'payment_status', 'payment_method', 'transaction_id', 'coupon', 'coupon_code',
            'shipping_address', 'billing_address', 'notes', 'shipped_at', 'delivered_at',
            'tenant', 'is_deleted', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'order_number', 'customer', 'subtotal', 'discount_amount', 'tax_amount', 'total_price', 'tenant', 'is_deleted', 'created_at', 'updated_at']

    def get_item_count(self, obj):
        return obj.items.count()


class OrderCreateSerializer(serializers.Serializer):
    items = serializers.ListField(child=serializers.DictField(), min_length=1)
    shipping_address = serializers.CharField(required=False, allow_blank=True)
    billing_address = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)
    coupon_code = serializers.CharField(required=False, allow_blank=True)
    shipping_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, default=0)

    def validate_items(self, value):
        for item in value:
            if 'product_id' not in item:
                raise serializers.ValidationError("Each item must have a product_id")
            if 'quantity' not in item or item['quantity'] < 1:
                raise serializers.ValidationError("Each item must have a quantity >= 1")
        return value

    @transaction.atomic
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        coupon_code = validated_data.pop('coupon_code', None)
        user = self.context['request'].user
        
        coupon = None
        if coupon_code:
            try:
                coupon = Coupon.objects.get(tenant=user.tenant, code=coupon_code, is_deleted=False)
                if not coupon.is_valid:
                    raise serializers.ValidationError("Coupon is not valid")
            except Coupon.DoesNotExist:
                raise serializers.ValidationError("Coupon not found")
        
        order = Order.objects.create(
            customer=user,
            tenant=user.tenant,
            coupon=coupon,
            shipping_address=validated_data.get('shipping_address', ''),
            billing_address=validated_data.get('billing_address', ''),
            notes=validated_data.get('notes', ''),
            shipping_amount=validated_data.get('shipping_amount', 0)
        )
        
        for item_data in items_data:
            product = Product.objects.get(id=item_data['product_id'], tenant=user.tenant, is_deleted=False)
            variant = None
            if 'variant_id' in item_data:
                variant = ProductVariant.objects.get(id=item_data['variant_id'], product=product)
            
            quantity = item_data['quantity']
            
            if variant:
                if variant.stock < quantity:
                    raise serializers.ValidationError(f"Insufficient stock for {product.name} - {variant.name}")
                variant.stock -= quantity
                variant.save()
            else:
                if product.stock < quantity:
                    raise serializers.ValidationError(f"Insufficient stock for {product.name}")
                product.stock -= quantity
                product.save()
            
            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                quantity=quantity,
                price_at_purchase=variant.price if variant else product.price
            )
        
        if coupon:
            coupon.usage_count += 1
            coupon.save()
        
        order.calculate_total()
        return order


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = AuditLog
        fields = ['id', 'user', 'user_name', 'action', 'model_name', 'object_id', 'changes', 'ip_address', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class SalesReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesReport
        fields = [
            'id', 'period_type', 'period_start', 'period_end', 'total_orders', 'total_revenue',
            'total_items_sold', 'average_order_value', 'new_customers', 'top_products', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DashboardSerializer(serializers.Serializer):
    total_products = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_customers = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_orders = serializers.IntegerField()
    low_stock_products = serializers.IntegerField()
    recent_orders = OrderSerializer(many=True)
    top_products = serializers.ListField()
    revenue_by_status = serializers.DictField()


class ApplyCouponSerializer(serializers.Serializer):
    code = serializers.CharField()
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
