"""
Multi-tenant middleware that identifies the current company
based on subdomain, custom domain, or user session.
"""
from django.http import HttpRequest


class CompanyMiddleware:
    """
    Middleware to identify the current company for multi-tenant support.
    Identification priority:
    1. User's company (if authenticated)
    2. Subdomain (e.g., company.printflow.com)
    3. Custom domain
    4. X-Company-ID header
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        company = self.get_company_from_request(request)
        request.company = company
        response = self.get_response(request)
        return response
    
    def get_company_from_request(self, request: HttpRequest):
        """Identify company from various sources."""
        from companies.models import Company
        
        # 1. Authenticated user's company
        if hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request.user, 'company') and request.user.company:
                return request.user.company
        
        # 2. X-Company-ID header
        company_id = request.headers.get('X-Company-ID')
        if company_id:
            try:
                return Company.objects.get(id=company_id, is_active=True)
            except Company.DoesNotExist:
                pass
        
        # 3. X-Company-Slug header
        company_slug = request.headers.get('X-Company-Slug')
        if company_slug:
            try:
                return Company.objects.get(slug=company_slug, is_active=True)
            except Company.DoesNotExist:
                pass
        # 4. Subdomain
        host = request.get_host().split(':')[0]
        parts = host.split('.')
        
        if len(parts) >= 2:
            subdomain = parts[0]
            if subdomain not in ['www', 'api', 'admin', 'app']:
                try:
                    return Company.objects.get(subdomain=subdomain, is_active=True)
                except Company.DoesNotExist:
                    pass
        
        # 5. Custom domain
        try:
            return Company.objects.filter(
                custom_domain=host,
                is_active=True
            ).first()
        except:
            pass
        
        return None                
        