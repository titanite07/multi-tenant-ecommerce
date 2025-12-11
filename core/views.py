from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Tenant, User, Product, Order
from .serializers import TenantSerializer, UserSerializer, ProductSerializer, OrderSerializer
from .permissions import TenantPermission, TenantProductPermission, TenantOrderPermission


class TenantAwareViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return self.queryset.none()
        if not self.request.user.tenant:
            return self.queryset.none()
        return self.queryset.filter(tenant=self.request.user.tenant)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant)


class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [TenantPermission]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Tenant.objects.none()
        if not self.request.user.tenant:
            return Tenant.objects.none()
        return Tenant.objects.filter(id=self.request.user.tenant.id)


class ProductViewSet(TenantAwareViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [TenantProductPermission]


class OrderViewSet(TenantAwareViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [TenantOrderPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == 'customer':
            queryset = queryset.filter(customer=self.request.user)
        return queryset

    def perform_create(self, serializer):
        serializer.save(
            tenant=self.request.user.tenant,
            customer=self.request.user
        )


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
