from django.conf import settings


def build_invitation_url(invitation):
    """
    Build invitation URL for COMPANY USERS ONLY
    (designer, printer, client)
    """

    company = invitation.company

    # LOCAL DEVELOPMENT
    if settings.DEBUG:
        return f"http://localhost:5173/accept-invitation/{invitation.token}"

    #PRODUCTION (SUBDOMAIN)
    return f"https://{company.slug}.printflow.com/accept-invitation/{invitation.token}" 