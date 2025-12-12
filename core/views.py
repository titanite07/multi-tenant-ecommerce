from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, F, Avg
from django.db import models
from django.utils import timezone
from datetime import timedelta
from .models import (
    Tenant, User, Product, Order, OrderItem, Category, AuditLog,
    ProductVariant, ProductImage, ProductReview, Wishlist, WishlistItem,
    Cart, CartItem, Coupon, ShippingAddress, SalesReport
)
from .serializers import (
    TenantSerializer, UserSerializer, ProductSerializer, OrderSerializer,
    OrderCreateSerializer, CategorySerializer, AuditLogSerializer, DashboardSerializer,
    ProductVariantSerializer, ProductImageSerializer, ProductReviewSerializer,
    WishlistSerializer, WishlistItemSerializer, CartSerializer, CartItemSerializer,
    CouponSerializer, ShippingAddressSerializer, SalesReportSerializer, ApplyCouponSerializer
)
from .permissions import TenantPermission, TenantProductPermission, TenantOrderPermission
from .filters import ProductFilter, OrderFilter, CategoryFilter, AuditLogFilter


class TenantAwareViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return self.queryset.none()
        if not self.request.user.tenant:
            return self.queryset.none()
        return self.queryset.filter(tenant=self.request.user.tenant, is_deleted=False)

    def perform_create(self, serializer):
        instance = serializer.save(tenant=self.request.user.tenant)
        self.log_action('create', instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.log_action('update', instance)

    def perform_destroy(self, instance):
        instance.is_deleted = True
        instance.save()
        self.log_action('delete', instance)

    def log_action(self, action, instance):
        ip = self.request.META.get('REMOTE_ADDR')
        AuditLog.objects.create(
            tenant=self.request.user.tenant,
            user=self.request.user,
            action=action,
            model_name=instance.__class__.__name__,
            object_id=instance.id,
            changes={},
            ip_address=ip
        )


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


class CategoryViewSet(TenantAwareViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [TenantProductPermission]
    filterset_class = CategoryFilter
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']

    @action(detail=False, methods=['get'])
    def tree(self, request):
        categories = self.get_queryset().filter(parent__isnull=True)
        serializer = self.get_serializer(categories, many=True)
        return Response(serializer.data)


class ProductViewSet(TenantAwareViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [TenantProductPermission]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'sku', 'barcode']
    ordering_fields = ['name', 'price', 'stock', 'created_at']

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        products = self.get_queryset().filter(stock__lte=F('min_stock_threshold'))
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        products = self.get_queryset().filter(is_featured=True)
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_stock(self, request, pk=None):
        product = self.get_object()
        quantity = request.data.get('quantity', 0)
        action_type = request.data.get('action', 'add')
        
        if action_type == 'add':
            product.stock += int(quantity)
        elif action_type == 'subtract':
            product.stock = max(0, product.stock - int(quantity))
        elif action_type == 'set':
            product.stock = max(0, int(quantity))
        
        product.save()
        self.log_action('update', product)
        return Response(self.get_serializer(product).data)

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        product = self.get_object()
        reviews = product.reviews.filter(is_approved=True)
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ProductReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = ProductReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [TenantProductPermission]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return ProductVariant.objects.none()
        return ProductVariant.objects.filter(product__tenant=self.request.user.tenant)


class ProductReviewViewSet(TenantAwareViewSet):
    queryset = ProductReview.objects.all()
    serializer_class = ProductReviewSerializer
    search_fields = ['title', 'comment']
    ordering_fields = ['rating', 'created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == 'customer':
            return queryset.filter(customer=self.request.user)
        return queryset

    def perform_create(self, serializer):
        product = serializer.validated_data['product']
        has_purchased = OrderItem.objects.filter(
            order__customer=self.request.user,
            product=product,
            order__status='delivered'
        ).exists()
        serializer.save(
            tenant=self.request.user.tenant,
            customer=self.request.user,
            is_verified_purchase=has_purchased
        )

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        review = self.get_object()
        if request.user.role not in ['owner', 'staff']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        review.is_approved = True
        review.save()
        return Response(self.get_serializer(review).data)


class WishlistViewSet(TenantAwareViewSet):
    queryset = Wishlist.objects.all()
    serializer_class = WishlistSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Wishlist.objects.none()
        return Wishlist.objects.filter(
            tenant=self.request.user.tenant,
            customer=self.request.user,
            is_deleted=False
        )

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.user.tenant, customer=self.request.user)

    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        wishlist = self.get_object()
        product_id = request.data.get('product_id')
        try:
            product = Product.objects.get(id=product_id, tenant=self.request.user.tenant, is_deleted=False)
            WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
            return Response(self.get_serializer(wishlist).data)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        wishlist = self.get_object()
        product_id = request.data.get('product_id')
        WishlistItem.objects.filter(wishlist=wishlist, product_id=product_id).delete()
        return Response(self.get_serializer(wishlist).data)


class CartViewSet(TenantAwareViewSet):
    queryset = Cart.objects.all()
    serializer_class = CartSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return Cart.objects.none()
        return Cart.objects.filter(tenant=self.request.user.tenant, customer=self.request.user, is_deleted=False)

    @action(detail=False, methods=['get'])
    def my_cart(self, request):
        cart, created = Cart.objects.get_or_create(
            tenant=request.user.tenant,
            customer=request.user,
            is_deleted=False
        )
        return Response(self.get_serializer(cart).data)

    @action(detail=False, methods=['post'])
    def add_item(self, request):
        cart, created = Cart.objects.get_or_create(
            tenant=request.user.tenant,
            customer=request.user,
            is_deleted=False
        )
        product_id = request.data.get('product_id')
        variant_id = request.data.get('variant_id')
        quantity = int(request.data.get('quantity', 1))
        
        try:
            product = Product.objects.get(id=product_id, tenant=request.user.tenant, is_deleted=False)
            variant = None
            if variant_id:
                variant = ProductVariant.objects.get(id=variant_id, product=product)
            
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                variant=variant,
                defaults={'quantity': quantity}
            )
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            return Response(self.get_serializer(cart).data)
        except Product.DoesNotExist:
            return Response({'error': 'Product not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def update_item(self, request):
        cart = Cart.objects.filter(tenant=request.user.tenant, customer=request.user, is_deleted=False).first()
        if not cart:
            return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)
        
        item_id = request.data.get('item_id')
        quantity = int(request.data.get('quantity', 1))
        
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            if quantity <= 0:
                cart_item.delete()
            else:
                cart_item.quantity = quantity
                cart_item.save()
            return Response(self.get_serializer(cart).data)
        except CartItem.DoesNotExist:
            return Response({'error': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['post'])
    def remove_item(self, request):
        cart = Cart.objects.filter(tenant=request.user.tenant, customer=request.user, is_deleted=False).first()
        if not cart:
            return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)
        
        item_id = request.data.get('item_id')
        CartItem.objects.filter(id=item_id, cart=cart).delete()
        return Response(self.get_serializer(cart).data)

    @action(detail=False, methods=['post'])
    def clear(self, request):
        cart = Cart.objects.filter(tenant=request.user.tenant, customer=request.user, is_deleted=False).first()
        if cart:
            cart.items.all().delete()
            return Response(self.get_serializer(cart).data)
        return Response({'error': 'Cart not found'}, status=status.HTTP_404_NOT_FOUND)


class CouponViewSet(TenantAwareViewSet):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [TenantProductPermission]
    search_fields = ['code', 'description']
    ordering_fields = ['valid_from', 'valid_until', 'created_at']

    @action(detail=False, methods=['post'])
    def validate(self, request):
        code = request.data.get('code')
        subtotal = request.data.get('subtotal', 0)
        
        try:
            coupon = Coupon.objects.get(
                tenant=request.user.tenant,
                code=code,
                is_deleted=False
            )
            if not coupon.is_valid:
                return Response({'error': 'Coupon is not valid', 'valid': False}, status=status.HTTP_400_BAD_REQUEST)
            
            discount = coupon.calculate_discount(float(subtotal))
            return Response({
                'valid': True,
                'coupon': CouponSerializer(coupon).data,
                'discount_amount': discount
            })
        except Coupon.DoesNotExist:
            return Response({'error': 'Coupon not found', 'valid': False}, status=status.HTTP_404_NOT_FOUND)


class ShippingAddressViewSet(TenantAwareViewSet):
    queryset = ShippingAddress.objects.all()
    serializer_class = ShippingAddressSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return ShippingAddress.objects.none()
        return ShippingAddress.objects.filter(
            tenant=self.request.user.tenant,
            customer=self.request.user,
            is_deleted=False
        )

    def perform_create(self, serializer):
        if serializer.validated_data.get('is_default'):
            ShippingAddress.objects.filter(
                customer=self.request.user,
                is_default=True
            ).update(is_default=False)
        serializer.save(tenant=self.request.user.tenant, customer=self.request.user)

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        address = self.get_object()
        ShippingAddress.objects.filter(customer=request.user, is_default=True).update(is_default=False)
        address.is_default = True
        address.save()
        return Response(self.get_serializer(address).data)


class OrderViewSet(TenantAwareViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [TenantOrderPermission]
    filterset_class = OrderFilter
    search_fields = ['order_number', 'customer__username', 'shipping_address']
    ordering_fields = ['created_at', 'total_price', 'status']

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role == 'customer':
            queryset = queryset.filter(customer=self.request.user)
        return queryset.prefetch_related('items', 'items__product')

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer

    def perform_create(self, serializer):
        order = serializer.save()
        AuditLog.objects.create(
            tenant=self.request.user.tenant,
            user=self.request.user,
            action='create',
            model_name='Order',
            object_id=order.id,
            changes={},
            ip_address=self.request.META.get('REMOTE_ADDR')
        )

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status not in dict(Order.STATUS_CHOICES):
            return Response({'error': 'Invalid status'}, status=status.HTTP_400_BAD_REQUEST)
        
        old_status = order.status
        order.status = new_status
        
        if new_status == 'shipped':
            order.shipped_at = timezone.now()
        elif new_status == 'delivered':
            order.delivered_at = timezone.now()
        
        order.save()
        
        AuditLog.objects.create(
            tenant=self.request.user.tenant,
            user=self.request.user,
            action='update',
            model_name='Order',
            object_id=order.id,
            changes={'status': {'old': old_status, 'new': new_status}},
            ip_address=self.request.META.get('REMOTE_ADDR')
        )
        
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=['post'])
    def update_payment(self, request, pk=None):
        order = self.get_object()
        payment_status = request.data.get('payment_status')
        transaction_id = request.data.get('transaction_id', '')
        payment_method = request.data.get('payment_method', '')
        
        if payment_status not in dict(Order.PAYMENT_STATUS_CHOICES):
            return Response({'error': 'Invalid payment status'}, status=status.HTTP_400_BAD_REQUEST)
        
        order.payment_status = payment_status
        order.transaction_id = transaction_id
        order.payment_method = payment_method
        order.save()
        
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        order = self.get_object()
        
        if order.status in ['shipped', 'delivered']:
            return Response({'error': 'Cannot cancel shipped or delivered orders'}, status=status.HTTP_400_BAD_REQUEST)
        
        for item in order.items.all():
            if item.variant:
                item.variant.stock += item.quantity
                item.variant.save()
            else:
                item.product.stock += item.quantity
                item.product.save()
        
        order.status = 'cancelled'
        order.save()
        
        return Response(self.get_serializer(order).data)

    @action(detail=False, methods=['get'])
    def my_orders(self, request):
        orders = self.get_queryset().filter(customer=request.user)
        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(orders, many=True)
        return Response(serializer.data)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [TenantPermission]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = AuditLogFilter
    ordering_fields = ['timestamp']

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return AuditLog.objects.none()
        if not self.request.user.tenant:
            return AuditLog.objects.none()
        return AuditLog.objects.filter(tenant=self.request.user.tenant)


class SalesReportViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SalesReport.objects.all()
    serializer_class = SalesReportSerializer
    permission_classes = [TenantPermission]

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return SalesReport.objects.none()
        return SalesReport.objects.filter(tenant=self.request.user.tenant)

    @action(detail=False, methods=['post'])
    def generate(self, request):
        period_type = request.data.get('period_type', 'daily')
        
        today = timezone.now().date()
        if period_type == 'daily':
            start_date = today - timedelta(days=1)
            end_date = today
        elif period_type == 'weekly':
            start_date = today - timedelta(days=7)
            end_date = today
        else:
            start_date = today.replace(day=1)
            end_date = today
        
        orders = Order.objects.filter(
            tenant=request.user.tenant,
            is_deleted=False,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            status='delivered'
        )
        
        total_orders = orders.count()
        total_revenue = orders.aggregate(total=Sum('total_price'))['total'] or 0
        total_items = OrderItem.objects.filter(order__in=orders).aggregate(total=Sum('quantity'))['total'] or 0
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        new_customers = User.objects.filter(
            tenant=request.user.tenant,
            role='customer',
            date_joined__date__gte=start_date,
            date_joined__date__lte=end_date
        ).count()
        
        top_products = list(OrderItem.objects.filter(order__in=orders).values(
            'product__id', 'product__name'
        ).annotate(
            total_sold=Sum('quantity')
        ).order_by('-total_sold')[:5])
        
        report, created = SalesReport.objects.update_or_create(
            tenant=request.user.tenant,
            period_type=period_type,
            period_start=start_date,
            defaults={
                'period_end': end_date,
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'total_items_sold': total_items,
                'average_order_value': avg_order_value,
                'new_customers': new_customers,
                'top_products': top_products
            }
        )
        
        return Response(SalesReportSerializer(report).data)


class DashboardView(generics.RetrieveAPIView):
    serializer_class = DashboardSerializer

    def get(self, request):
        if not request.user.is_authenticated or not request.user.tenant:
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)
        
        tenant = request.user.tenant
        
        products = Product.objects.filter(tenant=tenant, is_deleted=False)
        orders = Order.objects.filter(tenant=tenant, is_deleted=False)
        customers = User.objects.filter(tenant=tenant, role='customer')
        
        revenue_by_status = {}
        for status_choice in Order.STATUS_CHOICES:
            status_code = status_choice[0]
            total = orders.filter(status=status_code).aggregate(total=Sum('total_price'))['total'] or 0
            revenue_by_status[status_code] = float(total)
        
        top_products = list(OrderItem.objects.filter(
            order__tenant=tenant,
            order__is_deleted=False
        ).values(
            'product__id', 'product__name'
        ).annotate(
            total_sold=Sum('quantity'),
            total_revenue=Sum(F('price_at_purchase') * F('quantity'))
        ).order_by('-total_sold')[:5])
        
        data = {
            'total_products': products.count(),
            'total_orders': orders.count(),
            'total_customers': customers.count(),
            'total_revenue': orders.filter(status='delivered').aggregate(total=Sum('total_price'))['total'] or 0,
            'pending_orders': orders.filter(status='pending').count(),
            'low_stock_products': products.filter(stock__lte=F('min_stock_threshold')).count(),
            'recent_orders': OrderSerializer(orders[:5], many=True).data,
            'top_products': top_products,
            'revenue_by_status': revenue_by_status
        }
        
        return Response(data)


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]


class LogoutView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
            return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

