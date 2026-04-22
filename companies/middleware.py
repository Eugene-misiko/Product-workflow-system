"""
Multi-tenant middleware that identifies the current company (tenant)
based on the request's host (subdomain).

How it works:
- Extracts the host from the request (e.g. tenant1.example.com)
- Pulls the subdomain (tenant1)
- Looks up a Company with that slug
- Attaches it to request.tenant for use across the app

Fallback behavior:
- If running locally or no tenant found → request.tenant = None
"""

import logging

logger = logging.getLogger(__name__)


class TenantMiddleware:
    """Middleware to resolve tenant (Company) from request host."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.tenant = None
        try:
            host = request.get_host().split(":")[0]
            subdomain = host.split(".")[0]

            if subdomain not in ["localhost", "127", "0", "printflow"]:
                from companies.models import Company
                try:
                    request.tenant = Company.objects.get(slug=subdomain)
                except Company.DoesNotExist:
                    pass
        except:
            pass
        if not request.tenant and request.user.is_authenticated:
            request.tenant = request.user.company

        return self.get_response(request)
      