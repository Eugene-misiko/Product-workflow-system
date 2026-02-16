from django.shortcuts import render, get_object_or_404, redirect
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Payment, MethodPay, MpesaRequest, MpesaResponse
from .serializers import MpesaRequestSerializer, MpesaResponseSerializer
import requests, base64
from datetime import datetime
from orders.models import Order
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
def payment_create(request, order_id):
    from .forms import PaymentForm
    order = get_object_or_404(Order, id=order_id)

    if order.client != request.user:
        return render(request, "forbidden.html", status=403)

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.order = order
            payment.confirmed = False  # STK Push not confirmed yet
            payment.save()

            # Create MPESA request linked to this payment
            mpesa_request = MpesaRequest.objects.create(
                payment=payment,
                phone_number=form.cleaned_data['phone_number'],
                amount=payment.amount,
                account_reference=f"Order{order.id}",
                transaction_desc="Payment for order"
            )

            # Trigger STK Push
            response_data = initialize_stk_push(mpesa_request)
            MpesaResponse.objects.create(
                request=mpesa_request,
                merchant_request_id=response_data.get('MerchantRequestID', ''),
                checkout_request_id=response_data.get('CheckoutRequestID', ''),
                response_code=response_data.get('ResponseCode', ''),
                response_description=response_data.get('ResponseDescription', ''),
                customer_message=response_data.get('CustomerMessage', '')
            )

            return redirect("payment_list_template")
    else:
        form = PaymentForm()

    return render(request, "payment_form.html", {"form": form})
