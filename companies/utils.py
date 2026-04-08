from django.conf import settings

def build_invitation_url(invitation):
    """
    Build the correct invitation URL based on company domain or subdomain.

    Priority:
    1. Subdomain (e.g. zenith.localhost:5173 or zenith.printflow.com)
    2. Custom domain (e.g. zenith.com)
    3. Fallback to default FRONTEND_URL
    """
    company = invitation.company

    # LOCAL DEVELOPMENT (subdomain)
    if company.subdomain:
        return f"http://{company.subdomain}.localhost:5173/accept-invitation/{invitation.token}"

    # PRODUCTION CUSTOM DOMAIN
    if company.custom_domain:
        return f"https://{company.custom_domain}/accept-invitation/{invitation.token}"

    # FALLBACK
    return f"{settings.FRONTEND_URL}/accept-invitation/{invitation.token}"