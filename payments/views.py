import requests, base64
from datetime import datetime
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import MpesaRequest, MpesaResponse,Receipt
from .serializers import MpesaRequestSerializer, MpesaResponseSerializer
from django.shortcuts import render
from orders.models import Invoice
import logging
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
        "AccountReference": mpesa_request.account_reference or "Printing Payment",
        "TransactionDesc": mpesa_request.transaction_desc or "Printing Order Payment"
    }

    print("===== MPESA REQUEST =====")
    print("URL:", api_url)
    print("HEADERS:", headers)
    print("PAYLOAD:", payload)

    response = requests.post(api_url, json=payload, headers=headers)

    print("===== MPESA RESPONSE =====")
    print("STATUS CODE:", response.status_code)
    print("RAW RESPONSE:", response.text)

    try:
        return response.json()
    except Exception as e:
        print("JSON ERROR:", str(e))
        return {"error": "Invalid response from Safaricom", "raw": response.text}
@api_view(["POST"])
def stk_push(request):
   

    invoice_id = request.data.get("invoice_id")
    phone_number = request.data.get("phone_number")

    try:
        invoice = Invoice.objects.get(id=invoice_id)
    except Invoice.DoesNotExist:
        return Response({"error": "Invoice not found"}, status=404)

    order = invoice.order
    user = order.user

    # amount logic (deposit first)
    if invoice.status == "pending":
        amount = invoice.deposit_amount
    else:
        amount = invoice.balance_due

    mpesa_request = MpesaRequest.objects.create(
        user=user,
        order=order,
        invoice=invoice,
        phone_number=phone_number,
        amount=amount,
        account_reference=f"Order {order.id}",
        transaction_desc="Printing Order Payment"
    )

    response_data = initialize_stk_push(mpesa_request)

    if "MerchantRequestID" not in response_data:
        return Response(
            {"error": "Failed to connect to Safaricom", "details": response_data},
            status=status.HTTP_400_BAD_REQUEST
        )

    mpesa_response = MpesaResponse.objects.create(
        request=mpesa_request,
        merchant_request_id=response_data.get("MerchantRequestID"),
        checkout_request_id=response_data.get("CheckoutRequestID"),
        response_code=response_data.get("ResponseCode"),
        response_description=response_data.get("ResponseDescription"),
    )

    return Response(
        MpesaResponseSerializer(mpesa_response).data,
        status=status.HTTP_201_CREATED
    )
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
            invoice = mpesa_response.request.invoice
            order = mpesa_response.request.order
            user = mpesa_response.request.user
            if invoice.status == "pending":
                invoice.status = "partial"
                payment_type = "deposit"
            else:
                invoice.status = "paid"
                payment_type = "full"
            invoice.save()        
            metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])

            amount_paid = None
            mpesa_code = None
            for item in metadata:
                name = item.get("Name")
                value = item.get("Value")

                if name == "MpesaReceiptNumber":
                    mpesa_code = value
                    mpesa_response.receipt_number = value
                if name == "Amount":
                    amount_paid = value
            mpesa_response.amount_paid = amount_paid 
            mpesa_response.save()

            #create Receipt
            Receipt.objects.create(
                user=user,
                order=order,
                mpesa_receipt=mpesa_code,
                amount_paid=amount_paid,
                payment_type=payment_type
            )       

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

def download_receipt(request, receipt_id):

    receipt = Receipt.objects.get(id=receipt_id)

    return generate_receipt_pdf(receipt)