from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'owner'


class IsStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['owner', 'staff']


class IsCustomer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'customer'


class TenantProductPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.role == 'owner':
            return True
        
        if request.user.role == 'staff':
            return True
        
        if request.user.role == 'customer':
            return request.method in permissions.SAFE_METHODS
        
        return False

    def has_object_permission(self, request, view, obj):
        if not request.user.tenant:
            return False
        return obj.tenant == request.user.tenant


class TenantOrderPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        if request.user.role == 'owner':
            return True
        
        if request.user.role == 'staff':
            return True
        
        if request.user.role == 'customer':
            return request.method in permissions.SAFE_METHODS or request.method == 'POST'
        
        return False

    def has_object_permission(self, request, view, obj):
        if not request.user.tenant:
            return False
        
        if obj.tenant != request.user.tenant:
            return False
        
        if request.user.role == 'customer' and obj.customer != request.user:
            if request.method not in permissions.SAFE_METHODS:
                return False
        
        return True


class TenantPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role == 'owner'

    def has_object_permission(self, request, view, obj):
        if not request.user.tenant:
            return False
        return obj == request.user.tenant
