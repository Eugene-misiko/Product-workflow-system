from rest_framework.permissions import BasePermission

class CanAccessOrder(BasePermission):
    """
    Client can access own orders.
    Admin can access all orders.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.role == "admin":
            return True
        return obj.client == request.user
