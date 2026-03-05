from django.db import models

class MpesaRequest(models.Model):
    phone_number = models.CharField(max_length=15)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    account_reference = models.CharField(max_length=50)
    transaction_desc = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.phone_number} - {self.amount}"

class MpesaResponse(models.Model):
    # Changed to OneToOne for better data integrity
    request = models.OneToOneField(MpesaRequest, on_delete=models.CASCADE, related_name='response')
    
    # Identifiers from Safaricom
    merchant_request_id = models.CharField(max_length=255) 
    checkout_request_id = models.CharField(max_length=255, unique=True) # unique=True is vital for lookups
    
    # Initial Response data
    response_code = models.CharField(max_length=10) 
    response_description = models.CharField(max_length=255) 
    customer_message = models.CharField(max_length=255)
    
    # --- NEW FIELDS FOR CALLBACK DATA ---
    is_successful = models.BooleanField(default=False)
    receipt_number = models.CharField(max_length=50, null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    transaction_date = models.CharField(max_length=50, null=True, blank=True)
    # ------------------------------------

    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Paid" if self.is_successful else "Pending/Failed"
        return f"{self.checkout_request_id} - {status}"