import requests, base64
from datetime import datetime
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import MpesaRequest, MpesaResponse
from .serializers import MpesaRequestSerializer, MpesaResponseSerializer
from django.shortcuts import render

def get_mpesa_url(endpoint):
    """Helper to switch between Sandbox and Production URLs"""
    base = "https://api.safaricom.co.ke" if settings.MPESA_ENVIRONMENT == 'production' else "https://sandbox.safaricom.co.ke"
    return f"{base}/{endpoint}"

@api_view(['POST'])
def stk_push(request):
    serializer = MpesaRequestSerializer(data=request.data)
    if serializer.is_valid():
        mpesa_request = serializer.save()
        response_data = initialize_stk_push(mpesa_request)
        
        if 'MerchantRequestID' not in response_data:
            return Response({"error": "Safaricom connection failed", "details": response_data}, status=400)

        mpesa_response = MpesaResponse.objects.create(
            request = mpesa_request,
            merchant_request_id = response_data.get('MerchantRequestID', ''),
            checkout_request_id = response_data.get('CheckoutRequestID', ''),
            response_code = response_data.get('ResponseCode', ''),
            response_description = response_data.get('ResponseDescription', ''),
            customer_message = response_data.get('CustomerMessage', '')
        )
        
        return Response(MpesaResponseSerializer(mpesa_response).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def initialize_stk_push(mpesa_request):
    access_token = get_access_token()
    api_url = get_mpesa_url('mpesa/stkpush/v1/processrequest')#https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    password = generate_password(timestamp)
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
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
        "AccountReference": mpesa_request.account_reference or "Payment",
        "TransactionDesc": mpesa_request.transaction_desc or "STK Push"
    }
    
    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()

def get_access_token():
    api_url = get_mpesa_url("oauth/v1/generate?grant_type=client_credentials")
    response = requests.get(api_url, auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET))
    return response.json().get('access_token')

def generate_password(timestamp):
    # Using your specific EXPRESS_SHORTCODE variable
    data_to_encode = settings.MPESA_EXPRESS_SHORTCODE + settings.MPESA_PASSKEY + timestamp
    return base64.b64encode(data_to_encode.encode()).decode('utf-8')

def initiate_payment_view(request):
    """Renders the frontend template for the user to key in details"""
    # You can pass context like default amount if needed
    return render(request, 'stk_push_form.html')

@api_view(['POST'])
def mpesa_callback(request):
    data = request.data
    stk_callback = data.get('Body', {}).get('stkCallback', {})
    result_code = stk_callback.get('ResultCode')
    checkout_request_id = stk_callback.get('CheckoutRequestID')

    try:
        mpesa_res = MpesaResponse.objects.get(checkout_request_id=checkout_request_id)
        if result_code == 0:
            mpesa_res.is_successful = True
            
            # Extracting metadata like Receipt Number
            metadata = stk_callback.get('CallbackMetadata', {}).get('Item', [])
            for item in metadata:
                name = item.get('Name')
                value = item.get('Value')
                if name == 'MpesaReceiptNumber':
                    mpesa_res.receipt_number = value 
        else:
            mpesa_res.is_successful = False
            
        mpesa_res.save()
    except MpesaResponse.DoesNotExist:
        # Log this for debugging
        pass 

    return Response({"ResultCode": 0, "ResultDesc": "Success"})

import logging

# Configure logging to see what Safaricom sends during testing
logger = logging.getLogger(__name__)

@api_view(['POST'])
def mpesa_callback(request):
    """
    Handle the M-Pesa Callback after the user enters their PIN.
    """
    stk_callback_response = request.data.get('Body', {}).get('stkCallback', {})
    
    # Extract IDs to find our original record
    merchant_request_id = stk_callback_response.get('MerchantRequestID')
    checkout_request_id = stk_callback_response.get('CheckoutRequestID')
    result_code = stk_callback_response.get('ResultCode')
    result_desc = stk_callback_response.get('ResultDesc')

    # Find the MpesaResponse record we created during the push
    try:
        mpesa_response = MpesaResponse.objects.get(
            merchant_request_id=merchant_request_id,
            checkout_request_id=checkout_request_id
        )
        
        # Update the description with the final result
        mpesa_response.response_description = f"Result: {result_code} - {result_desc}"
        mpesa_response.response_code = str(result_code)
        mpesa_response.save()

        # If ResultCode is 0, the payment was successful
        if result_code == 0:
            # Extract metadata (Amount, Receipt, Phone)
            metadata = stk_callback_response.get('CallbackMetadata', {}).get('Item', [])
            # You can loop through metadata to find 'MpesaReceiptNumber' if needed
            logger.info(f"Payment Successful for {checkout_request_id}")
        else:
            logger.warning(f"Payment Failed/Cancelled: {result_desc}")

    except MpesaResponse.DoesNotExist:
        logger.error(f"Response record not found for {checkout_request_id}")

    # Safaricom expects a success response to stop retrying the callback
    return Response({"ResultCode": 0, "ResultDesc": "Success"}, status=status.HTTP_200_OK)