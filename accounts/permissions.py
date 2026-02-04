from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.role.name == "ADMIN"


class IsClient(BasePermission):
    def has_permission(self, request, view):
        return request.user.role.name == "CLIENT"


class IsDesigner(BasePermission):
    def has_permission(self, request, view):
        return request.user.role.name == "DESIGNER"
