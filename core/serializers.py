from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import Tenant, User, Product, Order


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['tenant_id'] = user.tenant.id if user.tenant else None
        token['role'] = user.role
        return token


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['id', 'name', 'subdomain', 'owner_email', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    tenant_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'role', 'tenant', 'tenant_id']
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


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'price', 'stock', 'tenant', 'created_at', 'updated_at']
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at']


class OrderSerializer(serializers.ModelSerializer):
    products = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Product.objects.all()
    )

    class Meta:
        model = Order
        fields = ['id', 'customer', 'products', 'total_price', 'status', 'tenant', 'created_at', 'updated_at']
        read_only_fields = ['id', 'customer', 'tenant', 'created_at', 'updated_at']

    def create(self, validated_data):
        products_data = validated_data.pop('products', [])
        order = Order.objects.create(**validated_data)
        order.products.set(products_data)
        total = sum(product.price for product in products_data)
        order.total_price = total
        order.save()
        return order

    def update(self, instance, validated_data):
        products_data = validated_data.pop('products', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if products_data is not None:
            instance.products.set(products_data)
            instance.total_price = sum(product.price for product in products_data)
        instance.save()
        return instance
