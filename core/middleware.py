import logging
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger('core')


class CacheMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        return response


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        logger.info(
            f"Request: {request.method} {request.path} "
            f"User: {getattr(request.user, 'username', 'Anonymous')} "
            f"IP: {self.get_client_ip(request)}"
        )
        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


def get_cache_key(prefix, tenant_id, **kwargs):
    key_parts = [prefix, str(tenant_id)]
    for k, v in sorted(kwargs.items()):
        key_parts.append(f'{k}_{v}')
    return ':'.join(key_parts)


def cache_products_list(tenant_id, page=1, queryset=None):
    cache_key = get_cache_key('products_list', tenant_id, page=page)
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data
    if queryset is not None:
        cache.set(cache_key, list(queryset), settings.CACHE_TTL.get('products', 300))
        return queryset
    return None


def cache_categories(tenant_id, queryset=None):
    cache_key = get_cache_key('categories', tenant_id)
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data
    if queryset is not None:
        cache.set(cache_key, list(queryset), settings.CACHE_TTL.get('categories', 900))
        return queryset
    return None


def cache_dashboard(tenant_id, data=None):
    cache_key = get_cache_key('dashboard', tenant_id)
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        return cached_data
    if data is not None:
        cache.set(cache_key, data, settings.CACHE_TTL.get('dashboard', 60))
        return data
    return None


def invalidate_tenant_cache(tenant_id):
    cache_keys = [
        get_cache_key('products_list', tenant_id),
        get_cache_key('categories', tenant_id),
        get_cache_key('dashboard', tenant_id),
        get_cache_key('featured_products', tenant_id),
    ]
    for key in cache_keys:
        cache.delete(key)
    logger.info(f'Cache invalidated for tenant {tenant_id}')


def cache_get_or_set(key, callback, timeout=300):
    cached_data = cache.get(key)
    if cached_data is not None:
        return cached_data
    data = callback()
    cache.set(key, data, timeout)
    return data
