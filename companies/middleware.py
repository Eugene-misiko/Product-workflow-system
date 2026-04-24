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
from django.utils.decorators import sync_and_async_middleware
from asgiref.sync import sync_to_async
from companies.models import Company

logger = logging.getLogger(__name__)

@sync_and_async_middleware
def TenantMiddleware(get_response):
    # This logic handles both Sync (manage.py) and Async (Daphne)
    
    if is_async := iscoroutinefunction(get_response):
        async def middleware(request):
            await resolve_tenant(request)
            response = await get_response(request)
            return response
    else:
        def middleware(request):
            resolve_tenant_sync(request)
            response = get_response(request)
            return response

    return middleware

def resolve_tenant_sync(request):
    request.tenant = None
    try:
        # Fixed the host splitting logic
        host = request.get_host().split(":")[0]
        subdomain = host.split(".")[0]

        if subdomain not in ["localhost", "127", "0", "printflow"]:
            request.tenant = Company.objects.filter(slug=subdomain).first()
    except Exception as e:
        logger.error(f"Tenant resolution error: {e}")
    
    if not request.tenant and request.user.is_authenticated:
        request.tenant = getattr(request.user, 'company', None)

async def resolve_tenant(request):
    # Wrap the sync logic for the async loop
    await sync_to_async(resolve_tenant_sync)(request)

# Helper needed for the decorator
from inspect import iscoroutinefunction



      