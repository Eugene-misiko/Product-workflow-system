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
    """
    Middleware to resolve tenant from subdomain.
    Attaches:
        request.tenant
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Lazy import 
        try:
            from companies.models import Company
        except ImportError as e:
            logger.error(f"Failed to import Company model: {e}")
            request.tenant = None
            return self.get_response(request)

        try:
            host = request.get_host().split(":")[0]
            subdomain = host.split(".")[0]

            # Local dev handling
            if subdomain in ["localhost", "127", "0"]:
                request.tenant = None
            else:
                try:
                    request.tenant = Company.objects.get(slug=subdomain)
                except Company.DoesNotExist:
                    logger.warning(f"No tenant for subdomain: {subdomain}")
                    request.tenant = None

        except Exception as e:
            logger.error(f"Tenant middleware failed: {e}")
            request.tenant = None

        return self.get_response(request)
def __call__(self, request):
    """
    Main middleware entry point.

    Responsibilities:
    - Resolve the current tenant (Company) from the request host
    - Attach the tenant instance to request.tenant
    - Gracefully handle missing tenants or errors
    - Always allow the request to continue

    Resolution logic:
    1. Extract hostname from request (remove port if present)
    2. Derive subdomain (e.g. tenant1.example.com → tenant1)
    3. If running locally → skip tenant resolution
    4. Attempt to fetch Company by slug=subdomain
    5. If not found → set request.tenant = None

    Fallback:
    - Any failure results in request.tenant = None
    """

    # Import here to avoid circular import issues
    try:
        from companies.models import Company
    except ImportError as e:
        logger.error(f"[TenantMiddleware] Import error: {e}")
        request.tenant = None
        return self.get_response(request)

    try:
        # Extract hostname (strip port if exists)
        host = request.get_host().split(":")[0]

        # Extract subdomain
        # Example: tenant1.example.com - > tenant1
        subdomain = host.split(".")[0]

        # Handle local development environments
        if subdomain in ["localhost", "127", "0"]:
            request.tenant = None

        else:
            try:
                # Attempt to resolve tenant using slug
                request.tenant = Company.objects.get(slug=subdomain)

            except Company.DoesNotExist:
                logger.warning(
                    f"[TenantMiddleware] No tenant found for subdomain: {subdomain}"
                )
                request.tenant = None

    except Exception as e:
        logger.error(f"[TenantMiddleware] Unexpected error: {e}")
        request.tenant = None

    # Continue request processing
    return self.get_response(request)        