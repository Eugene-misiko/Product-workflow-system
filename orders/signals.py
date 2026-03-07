from django.db.models.signals import post_save
from django.dispatch import receiver
from decimal import Decimal
import uuid

from .models import Order, Invoice


@receiver(post_save, sender=Order)
def create_invoice(sender, instance, created, **kwargs):

    if created:

        total = instance.product.price * instance.quantity

        deposit = total * Decimal("0.70")

        balance = total - deposit

        Invoice.objects.create(
            order=instance,
            invoice_number=f"INV-{uuid.uuid4().hex[:8].upper()}",
            total_amount=total,
            deposit_amount=deposit,
            balance_due=balance,
        )