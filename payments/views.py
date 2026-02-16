from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response    
from rest_framework import status
import requests
import base64
from datetime import datetime
from django.conf import settings
from .models import MpesaRequest, MpesaResponse
from .serializers import MpesaResponseSerializer, MpesaRequestSerializer
# Create your views here.

@api_view(['POST'])
def stk_push(request):
    serializer = MpesaRequestSerializer(data=request.data)
    if serializer.is_valid():
        mpesa_request = serializer.save()
        response_data = initialize_stk_push(mpesa_request)
        mpesa_response = MpesaResponse.objects.create(
            request = mpesa_request,
            merchant_request_id = response_data.get('MerchantRequestID', ''),
            checkout_request_id = response_data.get('CheckoutRequestID', ''),
            response_code = response_data.get('ResponseCode', ''),
            response_description = response_data.get('ResponseDescription', ''),
            customer_message = response_data.get('CustomerMessage', '')
        )
        response_serializer = MpesaResponseSerializer(mpesa_response)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


def initialize_stk_push(mpesa_request):
    access_token = get_access_token(),
    api_url = 'https://from post in the app endpoints'
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    payload = {
        "copy all endpoint from the snippest"
        "password": generate_password(),
        "BusinessShortCode": settings.MPESA_SHORT_CODE,
        "Timestamp": datetime.now().strftime('%Y%m%d%H%M%S'),
        "Amount": float(mpesa_request.amount),
        "PartyA": mpesa_request.phone_number,
        "PartyB": settings.MPESA_SHORTCODE,
        "TransactionType": "CustomerPayBillOnline",
        "TransactionDesc":mpesa_request.transaction_desc,
        "PhoneNumber": mpesa_request.phone_number,
        "AccountReference": mpesa_request.account_reference,
        "CallBackURL" :"https://mydomain.com/mpesa"

    }

    response = requests.post(api_url, json=payload, headers=headers)
    return response
def get_access_token():
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    api_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(api_url, auth=(consumer_key, consumer_secret))
    access_token = response.json().get('access_token')
    return access_token

def generate_password():
    shortcode = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = shortcode + passkey + timestamp
    encoded_string = base64.b64encode(data_to_encode.encode())
    return encoded_string.decode('utf-8')