"""
Multi-tenant middleware that identifies the current company
based on subdomain, custom domain, or user session.
"""
from django.http import HttpRequest
from .models import Company

#middleware to trigger the backend know which company the request belongs to
class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]
        subdomain = host.split('.')[0]

        if subdomain in ["localhost", "127"]:
            request.tenant = None
        else:
            try:
                request.tenant = Company.objects.get(slug=subdomain)
            except Company.DoesNotExist:
                request.tenant = None

        return self.get_response(request)        