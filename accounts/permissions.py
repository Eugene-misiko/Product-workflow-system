from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "admin"


class IsClient(BasePermission):
    """
    Allows access only to client users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "client"


class IsDesigner(BasePermission):
    """
    Allows access only to designer users.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == "designer"


