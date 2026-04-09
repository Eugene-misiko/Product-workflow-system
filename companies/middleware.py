"""
Multi-tenant middleware that identifies the current company
based on subdomain, custom domain, or user session.
"""
from django.http import HttpRequest


class CompanyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.company = self.get_company_from_request(request)
        return self.get_response(request)

    def get_company_from_request(self, request: HttpRequest):
        from companies.models import Company

        host = request.get_host().split(":")[0]
        parts = host.split(".")

        # Subdomain (PRIMARY)
        if len(parts) >= 3:
            subdomain = parts[0]

            if subdomain not in ["www", "api", "admin"]:
                try:
                    return Company.objects.get(
                        slug=subdomain,
                        is_active=True
                    )
                except Company.DoesNotExist:
                    pass

        # Localhost support (acme.localhost)
        if len(parts) == 2 and parts[1] == "localhost":
            subdomain = parts[0]
            try:
                return Company.objects.get(
                    slug=subdomain,
                    is_active=True
                )
            except Company.DoesNotExist:
                pass

        #  Custom domain
        company = Company.objects.filter(
            custom_domain=host,
            is_active=True
        ).first()

        if company:
            return company

        # Authenticated user fallback
        if hasattr(request, "user") and request.user.is_authenticated:
            if hasattr(request.user, "company") and request.user.company:
                return request.user.company


        return None