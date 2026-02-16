from django.db import models
from orders.models import Order
#create your models here

class MethodPay(models.Model):
    MPESA = "MPESA"
    VISA = "VISA"
    CASH = "CASH"

    MAKE_PAYMENT_THROUGH = [
        (MPESA, "Mpesa"),
        (VISA, "Visa"),
        (CASH, "Cash"),
    ]

    make_payment_through = models.CharField(
        max_length=10,
        choices=MAKE_PAYMENT_THROUGH,
        default=MPESA,
    )

    def __str__(self):
        return self.make_payment_through


class Payment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    method_of_payment = models.ForeignKey(MethodPay, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    confirmed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)


class MpesaRequest(models.Model):
    payment = models.OneToOneField(Payment, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    account_reference = models.CharField(max_length=50)
    transaction_desc = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)


class MpesaResponse(models.Model):
    request = models.ForeignKey(MpesaRequest, on_delete=models.CASCADE, related_name='responses')
    merchant_request_id = models.CharField(max_length=255)
    checkout_request_id = models.CharField(max_length=255)
    response_code = models.CharField(max_length=10)
    response_description = models.CharField(max_length=255)
    customer_message = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
   
