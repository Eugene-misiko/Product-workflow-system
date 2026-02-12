from django.db import models
from orders.models import Order
# Create your models here.

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
    """Payments for orders"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    method_of_payment = models.ForeignKey(MethodPay, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    confirmed = models.BooleanField(default=False)
    
