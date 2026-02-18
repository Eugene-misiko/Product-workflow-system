from django.db import models
from cloudinary.models import CloudinaryField
class Category(models.Model):
    pass

class Product(models.Model):
    pass



class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.email


    