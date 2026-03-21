import base64
import requests
from datetime import datetime
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def get_mpesa_url(endpoint):
    """
    Get the full URL for an M-Pesa API endpoint.
    Switches between Sandbox and Production based on settings.
    """
    if settings.MPESA_ENVIRONMENT == 'production':
        base = "https://api.safaricom.co.ke"
    else:
        base = "https://sandbox.safaricom.co.ke"
    
    return f"{base}/{endpoint}"

def get_access_token():
    """
    Get OAuth access token from Safaricom.
    
    Makes a request to Safaricom's OAuth endpoint to get an
    access token for API authentication.
    
    """
    url = get_mpesa_url("oauth/v1/generate?grant_type=client_credentials")
    try:
        response = requests.get(
            url,
            auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET),
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        access_token = data.get('access_token')
        
        if access_token:
            logger.info("Successfully obtained M-Pesa access token")
            return access_token
        else:
            logger.error(f"Failed to get access token: {data}")
            return None
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting M-Pesa access token: {str(e)}")
        return None

