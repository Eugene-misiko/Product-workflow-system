from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Payment, MethodPay, MpesaRequest, MpesaResponse
from .serializers import MpesaRequestSerializer, MpesaResponseSerializer
import requests, base64
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order
from .forms import PaymentForm
from django.contrib.auth.decorators import login_required
#create your views here
# Payment list (client sees own, admin sees all)
def payments_list(request):
    if not request.user.is_authenticated:
        return render(request, "forbidden.html", status=403)

    if request.user.role == "admin":
        payments = Payment.objects.all()
    else:
        payments = Payment.objects.filter(order__client=request.user)
    
    return render(request, "payment_list.html", {"payments": payments})


# Create a payment
@login_required
def payment_create(request, order_id):
    """
    Create a payment for a specific order and trigger MPESA STK Push.
    - Client must own the order
    - Payment is initially unconfirmed until STK Push succeeds
    """
    order = get_object_or_404(Order, id=order_id)

    # Access control
    if order.client != request.user:
        return render(request, "forbidden.html", status=403)

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            # Save Payment instance first
            payment = form.save(commit=False)
            payment.order = order
            payment.confirmed = False  # STK Push pending
            payment.save()

            # Update order status to approved (optional: could wait until MPESA confirmation)
            order.status = "approved"
            order.save()

            # Create linked MPESA request
            mpesa_request = MpesaRequest.objects.create(
                phone_number=form.cleaned_data['phone_number'],
                amount=payment.amount,
                account_reference=f"Order{order.id}",
                transaction_desc="Payment for order"
            )

            # Trigger STK Push
            response_data = initialize_stk_push(mpesa_request)

            # Record MPESA response
            MpesaResponse.objects.create(
                request=mpesa_request,
                merchant_request_id=response_data.get('MerchantRequestID', ''),
                checkout_request_id=response_data.get('CheckoutRequestID', ''),
                response_code=response_data.get('ResponseCode', ''),
                response_description=response_data.get('ResponseDescription', ''),
                customer_message=response_data.get('CustomerMessage', '')
            )

            # Redirect client to payments list or order detail
            return redirect("payment_list_template")
    else:
        form = PaymentForm()

    return render(request, "payment_form.html", {"form": form})

def get_access_token():
    consumer_key = settings.MPESA_CONSUMER_KEY
    consumer_secret = settings.MPESA_CONSUMER_SECRET
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(consumer_key, consumer_secret))
    return response.json().get('access_token')


def generate_password():
    shortcode = settings.MPESA_SHORTCODE
    passkey = settings.MPESA_PASSKEY
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    string_to_encode = shortcode + passkey + timestamp
    encoded_string = base64.b64encode(string_to_encode.encode())
    return encoded_string.decode('utf-8')


def initialize_stk_push(mpesa_request):
    access_token = get_access_token()
    api_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
    headers = {"Authorization": f"Bearer {access_token}"}
    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": generate_password(),
        "Timestamp": datetime.now().strftime('%Y%m%d%H%M%S'),
        "TransactionType": "CustomerPayBillOnline",
        "Amount": float(mpesa_request.amount),
        "PartyA": mpesa_request.phone_number,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": mpesa_request.phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": mpesa_request.account_reference,
        "TransactionDesc": mpesa_request.transaction_desc
    }

    response = requests.post(api_url, json=payload, headers=headers)
    return response.json()
@csrf_exempt
@api_view(['POST'])
def mpesa_callback(request):
    data = request.data.get('Body', {})
    stk_callback = data.get('stkCallback', {})
    checkout_request_id = stk_callback.get('CheckoutRequestID')
    result_code = stk_callback.get('ResultCode')
    result_desc = stk_callback.get('ResultDesc')

    mpesa_response = MpesaResponse.objects.filter(checkout_request_id=checkout_request_id).first()
    if mpesa_response:
        mpesa_response.response_code = result_code
        mpesa_response.response_description = result_desc
        mpesa_response.save()

        # Mark payment confirmed if successful
        if result_code == 0:
            payment = mpesa_response.request.payment
            payment.confirmed = True
            payment.order.status = "approved"
            payment.order.save()
            payment.save()

    return Response({"status": "success"})