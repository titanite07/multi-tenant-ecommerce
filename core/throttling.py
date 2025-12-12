from rest_framework.throttling import SimpleRateThrottle


class BurstRateThrottle(SimpleRateThrottle):
    scope = 'burst'

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}


class SustainedRateThrottle(SimpleRateThrottle):
    scope = 'sustained'

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}


class LoginRateThrottle(SimpleRateThrottle):
    scope = 'login'

    def get_cache_key(self, request, view):
        ident = self.get_ident(request)
        return self.cache_format % {'scope': self.scope, 'ident': ident}


class TenantRateThrottle(SimpleRateThrottle):
    scope = 'tenant'
    rate = '5000/hour'

    def get_cache_key(self, request, view):
        if request.user.is_authenticated and request.user.tenant:
            return self.cache_format % {'scope': self.scope, 'ident': request.user.tenant.pk}
        return None
