"""
Company Middleware - Multi-tenant support
Identifies the current company based on request
"""
from django.http import HttpRequest
from django.db import models
from typing import Optional

class CompanyMiddleware:
    """
    Middleware to identify the current company for multi-tenant support.
    
    The company can be identified by:
    1. Subdomain (e.g., company.printflow.com)
    2. Custom domain
    3. Header (X-Company-ID)
    4. User's company (if authenticated)
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Get company from various sources
        company = self.get_company_from_request(request)
        
        if company:
            request.company = company
        else:
            request.company = None
        
        response = self.get_response(request)
        return response
    
    def get_company_from_request(self, request: HttpRequest):
        """
        Determine the company from the request
        """
        from companies.models import Company
        
        # 1. Check for company header (for API requests)
        company_id = request.headers.get('X-Company-ID')
        if company_id:
            try:
                return Company.objects.get(id=company_id)
            except Company.DoesNotExist:
                pass
        
        # 2. Check subdomain
        host = request.get_host().split(':')[0]  # Remove port
        parts = host.split('.')
        
        if len(parts) >= 2:
            #  company.printflow.com
            subdomain = parts[0]
            if subdomain not in ['www', 'api', 'admin']:
                try:
                    return Company.objects.get(slug=subdomain)
                except Company.DoesNotExist:
                    pass
        
        # 3. Check custom domain
        try:
            return Company.objects.get(
                models.Q(custom_domain=host) | models.Q(custom_domain=f'www.{host}')
            )
        except Company.DoesNotExist:
            pass
        
        # 4. Check authenticated user's company
        if hasattr(request, 'user') and request.user.is_authenticated:
            return request.user.company
        
        return None


