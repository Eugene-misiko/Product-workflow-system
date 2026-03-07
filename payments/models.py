from django.db import models
from orders.models import Order
from accounts.models import User
import uuid
class MpesaRequest(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="payments")
    order = models.ForeignKey(Order,on_delete=models.CASCADE, related_name="payments")
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    account_reference = models.CharField(max_length=50)
    transaction_desc = models.CharField(max_length=255)
    invoice = models.ForeignKey("orders.Invoice", on_delete=models.CASCADE,related_name="payments")    
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.user.username} - Order {self.order.id}"

class MpesaResponse(models.Model):
    request = models.OneToOneField(MpesaRequest, on_delete=models.CASCADE,related_name="response")
    merchant_request_id = models.CharField(max_length=255)
    checkout_request_id = models.CharField(max_length=255, unique=True)
    response_code = models.CharField(max_length=10)
    response_description = models.CharField(max_length=255)
    is_successful = models.BooleanField(default=False)
    receipt_number = models.CharField(max_length=50, null=True, blank=True)
    amount_paid = models.DecimalField( max_digits=10,decimal_places=2,null=True,blank=True)
    transaction_date = models.CharField(max_length=50,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.checkout_request_id}"
    
class Receipt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    receipt_number = models.UUIDField(default=uuid.uuid4, editable=False)
    mpesa_receipt = models.CharField(max_length=100)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=[("deposit", "Deposit"),("full", "Full Payment")])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice {self.receipt_number}"  
      