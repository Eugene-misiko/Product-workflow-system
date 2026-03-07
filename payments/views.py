import requests, base64
from datetime import datetime
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import MpesaRequest, MpesaResponse, Invoice,Receipt
from .serializers import MpesaRequestSerializer, MpesaResponseSerializer
from django.shortcuts import render
import logging
from .utils import generate_invoice_pdf
from .utils import generate_receipt_pdf
 
logger = logging.getLogger(__name__)
def get_mpesa_url(endpoint):
    """
    Switch between Sandbox and Production
    """
    base = "https://api.safaricom.co.ke" if settings.MPESA_ENVIRONMENT == "production" else "https://sandbox.safaricom.co.ke"
    return f"{base}/{endpoint}"
def get_access_token():
    url = get_mpesa_url("oauth/v1/generate?grant_type=client_credentials")
    response = requests.get(
        url,
        auth=(settings.MPESA_CONSUMER_KEY, settings.MPESA_CONSUMER_SECRET)
    )
    return response.json().get("access_token")
def generate_password(timestamp):
    data = settings.MPESA_EXPRESS_SHORTCODE + settings.MPESA_PASSKEY + timestamp
    return base64.b64encode(data.encode()).decode("utf-8")
def initialize_stk_push(mpesa_request):
    access_token = get_access_token()
    api_url = get_mpesa_url("mpesa/stkpush/v1/processrequest")
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    password = generate_password(timestamp)
    headers = {
        "Authorization": f"Bearer {access_token}"
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
        "AccountReference": mpesa_request.account_reference or "Printing Payment",
        "TransactionDesc": mpesa_request.transaction_desc or "Printing Order Payment"
    }
    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()
@api_view(["POST"])
def stk_push(request):
    """
    Initiates STK Push
    """
    serializer = MpesaRequestSerializer(data=request.data)
    if serializer.is_valid():
        mpesa_request = serializer.save()
        response_data = initialize_stk_push(mpesa_request)
        if "MerchantRequestID" not in response_data:
            return Response(
                {
                    "error": "Failed to connect to Safaricom",
                    "details": response_data
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        mpesa_response = MpesaResponse.objects.create(
            request=mpesa_request,
            merchant_request_id=response_data.get("MerchantRequestID"),
            checkout_request_id=response_data.get("CheckoutRequestID"),
            response_code=response_data.get("ResponseCode"),
            response_description=response_data.get("ResponseDescription"),
            customer_message=response_data.get("CustomerMessage"),
        )
        return Response(
            MpesaResponseSerializer(mpesa_response).data,
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@api_view(["POST"])
def mpesa_callback(request):
    """
    Safaricom sends payment confirmation here
    """
    data = request.data
    stk_callback = data.get("Body", {}).get("stkCallback", {})

    merchant_request_id = stk_callback.get("MerchantRequestID")
    checkout_request_id = stk_callback.get("CheckoutRequestID")
    result_code = stk_callback.get("ResultCode")
    result_desc = stk_callback.get("ResultDesc")
    try:
        mpesa_response = MpesaResponse.objects.get(
            merchant_request_id=merchant_request_id,
            checkout_request_id=checkout_request_id
        )

        mpesa_response.response_code = str(result_code)
        mpesa_response.response_description = result_desc

        if result_code == 0:

            mpesa_response.is_successful = True

            metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])

            for item in metadata:
                name = item.get("Name")
                value = item.get("Value")

                if name == "MpesaReceiptNumber":
                    mpesa_response.receipt_number = value

            logger.info(f"Payment Successful: {checkout_request_id}")

        else:

            mpesa_response.is_successful = False

            logger.warning(f"Payment Failed: {result_desc}")

        mpesa_response.save()

    except MpesaResponse.DoesNotExist:

        logger.error(f"MpesaResponse not found for {checkout_request_id}")

    return Response(
        {"ResultCode": 0, "ResultDesc": "Success"},
        status=status.HTTP_200_OK
    )
def download_invoice(request, order_id):

    invoice = Invoice.objects.get(order_id=order_id)

    return generate_invoice_pdf(invoice)

def download_receipt(request, receipt_id):

    receipt = Receipt.objects.get(id=receipt_id)

    return generate_receipt_pdf(receipt)