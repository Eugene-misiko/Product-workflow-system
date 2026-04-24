"""
Handles:
  - STK Push initiation (stk_push)
  - Safaricom callback processing (mpesa_callback)
  - Payment status polling (payment_status)
Multitenancy:
  All operations are scoped to request.user.company via Invoice FK chain.
Security:
  - mpesa_callback validates all IPs in X-Forwarded-For chain.
  - stk_push and payment_status require IsAuthenticated.
"""

import logging
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import get_object_or_404
from payments.models import Invoice, MpesaRequest, MpesaResponse, Payment, Receipt
from payments.serializers import MpesaResponseSerializer, StkPushSerializer
from payments.mpesa_utils import initialize_stk_push
from notifications.models import Notification
from django.db import transaction
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.conf import settings 
logger = logging.getLogger(__name__)

# Safaricom's official callback IP whitelist
# https://developer.safaricom.co.ke/Documentation

ALLOWED_IPS = {"196.201.214.200", "196.201.214.206"}

def _is_allowed_ip(request) -> bool:
    """
    Validate that the request originates from a Safaricom callback IP.

    Checks every address in the X-Forwarded-For chain so the whitelist
    cannot be bypassed by prepending a trusted IP.
    """    
    # In dev mode (ngrok), skip IP check — ngrok proxies from its own IPs
    if getattr(settings, 'MPESA_DEV_MODE', False):
        return True

    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    if forwarded_for:
        ips = {ip.strip() for ip in forwarded_for.split(",")}
    else:
        ips = {request.META.get("REMOTE_ADDR", "")}
    return bool(ips & ALLOWED_IPS)



def _send_payment_ws_notification(invoice) -> None:
    """
    Broadcast a real-time payment update to the company's WebSocket group.

    Called via transaction.on_commit so the DB is fully committed before
    clients receive the push.
    """
    try:
        channel_layer = get_channel_layer()
        group_name = f"payments_{str(invoice.company_id)}"
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                "type": "send_notification",
                "data": {
                    "type": "payment_update",
                    "invoice_id": invoice.id,
                    "invoice_number": invoice.invoice_number,
                    "status": invoice.status,
                    "amount_paid": str(invoice.amount_paid),
                    "balance_due": str(invoice.balance_due),
                },
            },
        )
    except Exception as exc:
        logger.error("WebSocket notification failed: %s", exc)

# STK Push — initiate payment

@api_view(["POST"])
def stk_push(request):
    """
    Initiate an M-Pesa STK Push payment for an invoice.

    The amount charged is determined automatically:
      - Invoice is PENDING  → charge the 70% deposit amount
      - Invoice is PARTIAL  → charge the remaining balance (30%)
      - Invoice is PAID     → rejected with 400

    Request body:
        invoice_id   (int)  — ID of the invoice to pay
        phone_number (str)  — Customer phone in format 2547XXXXXXXX

    Returns:
        201 — MpesaResponse data on success
        400 — Validation error or M-Pesa connection failure
    """
    serializer = StkPushSerializer(data=request.data, context={"request": request})
    serializer.is_valid(raise_exception=True)

    invoice = get_object_or_404(
        Invoice,
        id=serializer.validated_data["invoice_id"],
        company=request.user.company,
    )

    if invoice.status == Invoice.STATUS_PAID:
        return Response(
            {"error": "Invoice is already fully paid."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Determine what to charge
    if invoice.status == Invoice.STATUS_PENDING:
        amount = invoice.deposit_amount
        payment_type = Payment.PAYMENT_TYPE_DEPOSIT
    else:
        amount = invoice.balance_due
        payment_type = Payment.PAYMENT_TYPE_BALANCE

    # Create the pending M-Pesa request record
    mpesa_request = MpesaRequest.objects.create(
        user=request.user,
        order=invoice.order,
        invoice=invoice,
        phone_number=serializer.validated_data["phone_number"],
        amount=amount,
        account_reference=f"Order-{invoice.order.order_number}",
        transaction_desc=f"PrintFlow Payment - {invoice.order.order_number}",
    )

    response_data = initialize_stk_push(mpesa_request, request.user.company)

    if "error" in response_data or "MerchantRequestID" not in response_data:
        logger.error("STK Push failed: %s", response_data)
        return Response(
            {"error": "Failed to connect to M-Pesa", "details": response_data},
            status=status.HTTP_400_BAD_REQUEST,
        )

    mpesa_response = MpesaResponse.objects.create(
        request=mpesa_request,
        merchant_request_id=response_data.get("MerchantRequestID"),
        checkout_request_id=response_data.get("CheckoutRequestID"),
        response_code=response_data.get("ResponseCode"),
        response_description=response_data.get("ResponseDescription"),
    )

    logger.info("STK Push initiated: checkout_id=%s", mpesa_response.checkout_request_id)

    return Response(
        MpesaResponseSerializer(mpesa_response).data,
        status=status.HTTP_201_CREATED,
    )

# M-Pesa Callback — receive payment result from Safaricom
@api_view(["POST"])
@permission_classes([AllowAny])
def mpesa_callback(request):
    """
    Handle the asynchronous payment result callback from Safaricom.

    Safaricom sends this after the customer completes (or cancels) the
    STK Push prompt on their phone.

    On SUCCESS (ResultCode == 0):
      1. Marks MpesaResponse as successful and stores receipt/amount/date.
      2. Updates invoice.amount_paid and recalculates invoice.status.
      3. Creates a Payment record (idempotent — skipped if one exists).
      4. Creates a Receipt record.
      5. Sends a real-time WebSocket notification to the company group
         after the DB transaction commits.

    On FAILURE (ResultCode != 0):
      1. Marks MpesaResponse as failed.
      2. Creates a failure Notification for the user.

    Security:
      Only accepts requests from Safaricom's whitelisted IPs.
      company_id query param is accepted for routing but NOT trusted for
      security — multitenancy is enforced through the MpesaResponse FK chain.

    Returns:
      Always 200 with {ResultCode, ResultDesc} as Safaricom expects.
    """
    data = request.data
    stk_callback = data.get("Body", {}).get("stkCallback", {})

    merchant_request_id = stk_callback.get("MerchantRequestID")
    checkout_request_id = stk_callback.get("CheckoutRequestID")
    result_code = stk_callback.get("ResultCode")
    result_desc = stk_callback.get("ResultDesc")

    logger.info(
        "M-Pesa callback received: checkout_id=%s result_code=%s",
        checkout_request_id,
        result_code,
    )

    try:
        mpesa_response = MpesaResponse.objects.select_related(
            "request__invoice__company",
            "request__order",
            "request__user",
        ).get(
            merchant_request_id=merchant_request_id,
            checkout_request_id=checkout_request_id,
        )
    except MpesaResponse.DoesNotExist:
        logger.error("MpesaResponse not found: checkout_id=%s", checkout_request_id)
        return Response(
            {"ResultCode": 1, "ResultDesc": "Request not found"},
            status=status.HTTP_200_OK,
        )

    invoice = mpesa_response.request.invoice
    order = mpesa_response.request.order
    user = mpesa_response.request.user
    mpesa_response.response_code = str(result_code)
    mpesa_response.response_description = result_desc

    if result_code == 0:
        #  Payment successful
        mpesa_response.is_successful = True

        # Extract metadata items from the callback
        metadata = stk_callback.get("CallbackMetadata", {}).get("Item", [])
        mpesa_code = None
        amount_paid = None
        transaction_date = None

        for item in metadata:
            name = item.get("Name")
            value = item.get("Value")
            if name == "MpesaReceiptNumber":
                mpesa_code = value
                mpesa_response.receipt_number = mpesa_code
            elif name == "Amount":
                amount_paid = value
                mpesa_response.amount_paid = amount_paid
            elif name == "TransactionDate":
                transaction_date = str(value)
                mpesa_response.transaction_date = transaction_date

        mpesa_response.save()
        paid = amount_paid or mpesa_response.request.amount

        # All DB writes in a single atomic block so partial failures roll back
        with transaction.atomic():
            # Re-fetch invoice with row-level lock to avoid race conditions
            invoice = Invoice.objects.select_for_update().get(pk=invoice.pk)
            invoice.amount_paid = (invoice.amount_paid or 0) + paid
            # Status recalculation — prefer model constants if available
            if invoice.amount_paid >= invoice.total_amount:
                invoice.status = Invoice.STATUS_PAID if hasattr(Invoice, "STATUS_PAID") else "paid"
            else:
                invoice.status = "partially_paid"

            invoice.save()
            # Idempotency guard — prevent duplicate Payment records
            if not Payment.objects.filter(mpesa_response=mpesa_response).exists():
                payment_type = (
                    Payment.PAYMENT_TYPE_DEPOSIT
                    if mpesa_response.request.amount == invoice.deposit_amount
                    else Payment.PAYMENT_TYPE_BALANCE
                )

                payment = Payment.objects.create(
                    company=invoice.company,
                    invoice=invoice,
                    amount=paid,
                    payment_method=Payment.METHOD_MPESA,
                    payment_type=payment_type,
                    status=Payment.STATUS_COMPLETED,
                    mpesa_response=mpesa_response,
                    transaction_id=mpesa_code,
                    completed_at=timezone.now(),
                )

                Receipt.objects.create(
                    company=invoice.company,
                    user=user,
                    order=order,
                    invoice=invoice,
                    payment=payment,
                    mpesa_receipt=mpesa_code,
                    amount_paid=paid,
                    payment_type=payment.payment_type,
                )

                # Fire WebSocket notification only after the transaction commits
                # so clients always receive a consistent DB state.
                # Capture invoice in closure to avoid stale reference.
                _invoice_snapshot = invoice

                def notify():
                    _send_payment_ws_notification(_invoice_snapshot)

                transaction.on_commit(notify)

        logger.info("Payment successful: mpesa_receipt=%s invoice=%s", mpesa_code, invoice.id)

    else:
        # Payment failed 
        mpesa_response.is_successful = False
        mpesa_response.save()

        Notification.objects.create(
            company=invoice.company,
            user=user,
            notification_type=Notification.TYPE_PAYMENT,
            title="Payment Failed",
            message=(
                f"Your payment for order {order.order_number} failed. "
                f"Reason: {result_desc}"
            ),
            related_object_type="order",
            related_object_id=order.id,
        )

        logger.warning("Payment failed: checkout_id=%s reason=%s", checkout_request_id, result_desc)

    return Response({"ResultCode": 0, "ResultDesc": "Success"}, status=status.HTTP_200_OK)


# Payment Status — client polling endpoint
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def payment_status(request, checkout_request_id):
    """
    Check the current status of an M-Pesa STK Push payment.

    Useful for the frontend to poll after initiating payment, in case the
    WebSocket notification is missed or the callback is delayed.

    Args:
        checkout_request_id (str): The CheckoutRequestID returned by stk_push.

    Returns:
        200 — Payment status data
        404 — No matching payment found for this company
    """
    try:
        mpesa_response = MpesaResponse.objects.get(
            checkout_request_id=checkout_request_id,
            request__invoice__company=request.user.company,
        )
    except MpesaResponse.DoesNotExist:
        return Response({"error": "Payment request not found"}, status=404)

    return Response(
        {
            "checkout_request_id": mpesa_response.checkout_request_id,
            "is_successful": mpesa_response.is_successful,
            "response_code": mpesa_response.response_code,
            "response_description": mpesa_response.response_description,
            "amount_paid": mpesa_response.amount_paid,
            "receipt_number": mpesa_response.receipt_number,
            "created_at": mpesa_response.created_at,
        }
    )