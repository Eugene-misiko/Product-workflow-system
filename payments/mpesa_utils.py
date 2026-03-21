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

def generate_password(timestamp):
    """
    Generate password for STK Push request.
    """
    data = f"{settings.MPESA_EXPRESS_SHORTCODE}{settings.MPESA_PASSKEY}{timestamp}"
    return base64.b64encode(data.encode()).decode("utf-8")

def initialize_stk_push(mpesa_request):
    """
    Initialize an M-Pesa STK Push request.
    Sends an STK Push request to Safaricom to prompt the user
    to enter their M-Pesa PIN on their phone.
    """
    access_token = get_access_token()
    
    if not access_token:
        return {
            'error': 'Failed to get access token',
            'details': 'Could not authenticate with Safaricom'
        }
    
    api_url = get_mpesa_url("mpesa/stkpush/v1/processrequest")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = generate_password(timestamp)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "BusinessShortCode": settings.MPESA_EXPRESS_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(mpesa_request.amount),
        "PartyA": mpesa_request.phone_number,
        "PartyB": settings.MPESA_EXPRESS_SHORTCODE,
        "PhoneNumber": mpesa_request.phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": mpesa_request.account_reference or "PrintFlow Payment",
        "TransactionDesc": mpesa_request.transaction_desc or "Printing Order Payment"
    }
    
    logger.info(f"STK Push Request: Phone={mpesa_request.phone_number}, Amount={mpesa_request.amount}")
    
    try:
        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        
        data = response.json()
        logger.info(f"STK Push Response: {data}")
        return data
        
    except requests.exceptions.RequestException as e:
        logger.error(f"STK Push Error: {str(e)}")
        return {
            'error': 'Request failed',
            'details': str(e)
        }
