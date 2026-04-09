from django.conf import settings

def build_invitation_url(invitation):
    """
    Build invitation URL for COMPANY USERS ONLY
    """

    company = invitation.company

    # Subdomain (PRIMARY)
    if company.subdomain:
        return f"http://{company.subdomain}.localhost:5173/accept-invitation/{invitation.token}"

    # Custom domain
    if company.custom_domain:
        return f"https://{company.custom_domain}/accept-invitation/{invitation.token}"

    # Fallback
    return f"{settings.FRONTEND_URL}/accept-invitation/{invitation.token}"