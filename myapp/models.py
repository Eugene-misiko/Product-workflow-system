from django.db import models
import uuid
# Create your models here.
class Book(models.Model):
    title = models.CharField(max_length=150)
    author = models.CharField(max_length=100)
    description = models.TextField()
    publisher = models.CharField(max_length=100)
    published_date = models.DateField(null=True, blank=True)
    page_count = models.PositiveIntegerField(null=True, blank=True)
    class BookFormat(models.TextChoices):
        HARDCOVER = 'HC', 'Hard Cover'
        PAPERBACK = 'PB', 'Paperback'
        EBOOK = 'EB', 'eBook'
    format = models.CharField(max_length=2, 
                              choices=BookFormat.choices,
                              default=BookFormat.HARDCOVER)
    price = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    