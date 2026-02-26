# permissions.py
from rest_framework import permissions

class IsAdminOrOwner(permissions.BasePermission):
    """
    Custom permission to allow:
    - Admin users to see/edit all orders
    - Regular users to see/edit only their own orders
    """

    def has_object_permission(self, request, view, obj):
        # Admin can do anything
        if request.user.role == 'admin':
            return True
        # Otherwise, only allow if the object belongs to the user
        return obj.user == request.user