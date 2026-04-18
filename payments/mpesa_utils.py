import base64
import requests
from django.utils import timezone
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

def generate_password(shortcode, timestamp):
    """
    Generate password for STK Push request.
    """
    data = f"{shortcode}{settings.MPESA_PASSKEY}{timestamp}"
    return base64.b64encode(data.encode()).decode("utf-8")
    def format_phone(phone):
        if phone.startswith("0"):
            return "254" + phone[1:]
        elif phone.startswith("+254"):
            return phone[1:]
        return phone
def initialize_stk_push(mpesa_request,company):
    """
    Initialize an M-Pesa STK Push request.
    Sends an STK Push request to Safaricom to prompt the user
    to enter their M-Pesa PIN on their phone.
    """
    if not all([
        company.mpesa_shortcode,
        settings.MPESA_PASSKEY,
        settings.MPESA_CONSUMER_KEY,
        settings.MPESA_CONSUMER_SECRET
    ]):
        return {"error": "M-Pesa not fully configured"}   
    access_token = get_access_token()
    
    if not access_token:
        return {
            'error': 'Failed to get access token',
            'details': 'Could not authenticate with Safaricom'
        }
    
    api_url = get_mpesa_url("mpesa/stkpush/v1/processrequest")
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    password = generate_password(company.mpesa_shortcode, timestamp)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    phone = format_phone(mpesa_request.phone_number)
    payload = {
        "BusinessShortCode": company.mpesa_shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(mpesa_request.amount),
        "PartyA": phone,
        "PartyB": company.mpesa_shortcode,
        "PhoneNumber": phone,
        "CallBackURL": f"{settings.MPESA_CALLBACK_URL}?company_id={company.id}",
        "AccountReference": mpesa_request.account_reference or "PrintFlow Payment",
        "TransactionDesc": mpesa_request.transaction_desc or "Printing Order Payment"
    }
    
    logger.info(f"STK Push Request: Phone={phone}, Amount={mpesa_request.amount}")
    
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



def query_stk_status(checkout_request_id, company):
    """
    Query the status of an STK Push request.
    
    """
    access_token = get_access_token()
    
    if not access_token:
        return {'error': 'Failed to get access token'}
    
    api_url = get_mpesa_url("mpesa/stkpushquery/v1/query")
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    password = generate_password(company.mpesa_shortcode, timestamp)
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "BusinessShortCode": company.mpesa_shortcode,
        "Password": password,
        "Timestamp": timestamp,
        "CheckoutRequestID": checkout_request_id
    }
    
    try:
        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=30
        )
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"STK Status Query Error: {str(e)}")
        return {'error': str(e)}