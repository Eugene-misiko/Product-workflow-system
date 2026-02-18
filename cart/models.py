from django.db import models
from myapp.models import Product
# Create your models here.
class Cart(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)

    def get_total_price(self):
        return sum(items.get_total_price() for item in self.items.all())

class CartItems(models.Model):
    cart = models.ForeignKey(Cart, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="cart_items",on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def get_total_price(self):
        return self.product.price * self.quantity