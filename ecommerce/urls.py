from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


def api_root(request):
    return JsonResponse({
        'message': 'Multi-Tenant E-Commerce API',
        'version': '1.0.0',
        'endpoints': {
            'auth': {
                'token': '/api/token/',
                'refresh': '/api/token/refresh/',
                'register': '/api/register/',
            },
            'resources': {
                'tenants': '/api/tenants/',
                'products': '/api/products/',
                'orders': '/api/orders/',
            },
            'admin': '/admin/',
        },
        'documentation': 'Use JWT Bearer token for authentication. Token includes tenant_id and role claims.',
    })


def health_check(request):
    return JsonResponse({'status': 'healthy'})


urlpatterns = [
    path('', api_root, name='api-root'),
    path('health/', health_check, name='health-check'),
    path('admin/', admin.site.urls),
    path('api/', include('core.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

