from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Count, F
from datetime import timedelta
import logging

logger = logging.getLogger('core')


@shared_task
def send_order_confirmation_email(order_id):
    from .models import Order
    try:
        order = Order.objects.select_related('customer', 'tenant').get(id=order_id)
        subject = f'Order Confirmation - {order.order_number}'
        message = f'''
Dear {order.customer.username},

Thank you for your order!

Order Number: {order.order_number}
Total Amount: ${order.total_price}
Status: {order.get_status_display()}

We will process your order shortly.

Best regards,
{order.tenant.name}
'''
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.customer.email],
            fail_silently=True,
        )
        logger.info(f'Order confirmation email sent for order {order_id}')
    except Order.DoesNotExist:
        logger.error(f'Order {order_id} not found for email')


@shared_task
def send_order_status_update_email(order_id, old_status, new_status):
    from .models import Order
    try:
        order = Order.objects.select_related('customer', 'tenant').get(id=order_id)
        subject = f'Order Status Update - {order.order_number}'
        message = f'''
Dear {order.customer.username},

Your order status has been updated.

Order Number: {order.order_number}
Previous Status: {old_status}
New Status: {new_status}

Best regards,
{order.tenant.name}
'''
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [order.customer.email],
            fail_silently=True,
        )
        logger.info(f'Order status update email sent for order {order_id}')
    except Order.DoesNotExist:
        logger.error(f'Order {order_id} not found for email')


@shared_task
def generate_daily_reports():
    from .models import Tenant, Order, SalesReport, User, OrderItem
    logger.info('Starting daily report generation')
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    
    for tenant in Tenant.objects.filter(is_active=True):
        orders = Order.objects.filter(
            tenant=tenant,
            is_deleted=False,
            created_at__date=yesterday,
            status='delivered'
        )
        
        total_orders = orders.count()
        total_revenue = orders.aggregate(total=Sum('total_price'))['total'] or 0
        total_items = OrderItem.objects.filter(order__in=orders).aggregate(total=Sum('quantity'))['total'] or 0
        avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
        
        new_customers = User.objects.filter(
            tenant=tenant,
            role='customer',
            date_joined__date=yesterday
        ).count()
        
        top_products = list(OrderItem.objects.filter(order__in=orders).values(
            'product__id', 'product__name'
        ).annotate(
            total_sold=Sum('quantity')
        ).order_by('-total_sold')[:5])
        
        SalesReport.objects.update_or_create(
            tenant=tenant,
            period_type='daily',
            period_start=yesterday,
            defaults={
                'period_end': yesterday,
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'total_items_sold': total_items,
                'average_order_value': avg_order_value,
                'new_customers': new_customers,
                'top_products': top_products
            }
        )
        logger.info(f'Daily report generated for {tenant.name}')
    
    logger.info('Daily report generation completed')


@shared_task
def check_low_stock_alerts():
    from .models import Product, Tenant
    logger.info('Checking low stock alerts')
    
    for tenant in Tenant.objects.filter(is_active=True):
        low_stock_products = Product.objects.filter(
            tenant=tenant,
            is_deleted=False,
            stock__lte=F('min_stock_threshold')
        )
        
        if low_stock_products.exists():
            product_list = ', '.join([p.name for p in low_stock_products[:10]])
            subject = f'Low Stock Alert - {tenant.name}'
            message = f'''
Low stock alert for {tenant.name}!

The following products are running low on stock:
{product_list}

Please restock soon.
'''
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [tenant.owner_email],
                fail_silently=True,
            )
            logger.info(f'Low stock alert sent for {tenant.name}')


@shared_task
def cleanup_expired_carts():
    from .models import Cart
    logger.info('Cleaning up expired carts')
    
    expiry_date = timezone.now() - timedelta(days=7)
    expired_carts = Cart.objects.filter(
        updated_at__lt=expiry_date,
        customer__isnull=True
    )
    count = expired_carts.count()
    expired_carts.delete()
    
    logger.info(f'Cleaned up {count} expired guest carts')


@shared_task
def process_order_async(order_id):
    from .models import Order
    try:
        order = Order.objects.get(id=order_id)
        order.calculate_total()
        send_order_confirmation_email.delay(order_id)
        logger.info(f'Order {order_id} processed asynchronously')
    except Order.DoesNotExist:
        logger.error(f'Order {order_id} not found')


@shared_task
def invalidate_product_cache(tenant_id):
    from django.core.cache import cache
    cache.delete(f'products_list_{tenant_id}')
    cache.delete(f'featured_products_{tenant_id}')
    logger.info(f'Product cache invalidated for tenant {tenant_id}')


@shared_task
def update_product_ratings(product_id):
    from .models import Product
    from django.db.models import Avg
    try:
        product = Product.objects.get(id=product_id)
        avg_rating = product.reviews.filter(is_approved=True).aggregate(avg=Avg('rating'))['avg']
        logger.info(f'Updated rating for product {product_id}: {avg_rating}')
    except Product.DoesNotExist:
        logger.error(f'Product {product_id} not found')
