from rest_framework.permissions import BasePermission
from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "admin"


class IsClient(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "client"


class IsDesigner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "designer"


class IsPrinter(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "printer"
