from rest_framework.permissions import BasePermission

class IsDesigner(BasePermission):
    """
    Only designers allowed.
    """
    def has_permission(self, request, view):
        return request.user.role == "designer"
