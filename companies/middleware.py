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
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware to resolve the current tenant (Company) from the request.
    Adds:
        request.tenant - Company instance or None
    """

    def process_request(self, request):
        """
        Process incoming request and attach tenant.
        """
        # Lazy import to avoid circular imports
        try:
            from companies.models import Company
        except ImportError as e:
            logger.error(f"Failed to import Company model: {e}")
            request.tenant = None
            return

        try:
            host = request.get_host().split(':')[0] 
            subdomain = host.split('.')[0]

            # Local environments
            if subdomain in ["localhost", "127", "0"]:
                request.tenant = None
                return
            # Attempt to find tenant
            try:
                request.tenant = Company.objects.get(slug=subdomain)

            except Company.DoesNotExist:
                logger.warning(
                    f"No tenant found for subdomain: {subdomain}"
                )
                request.tenant = None

        except Exception as e:
            logger.error(f"Tenant middleware failed: {e}")
            request.tenant = None