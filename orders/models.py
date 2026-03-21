from django.db import models
from django.conf import settings
from django.utils import timezone
import random
import string

def generate_order_number():
    date_part = timezone.now().strftime('%Y%m%d')
    random_part = ''.join(random.choices(string.digits, k=4))
    return f"ORD-{date_part}-{random_part}"


class Order(models.Model):
    """
    Main Order model with complete workflow tracking.
    """
    
    # Status choices
    STATUS_PENDING = 'pending'
    STATUS_ASSIGNED_TO_DESIGNER = 'assigned_to_designer'
    STATUS_DESIGN_IN_PROGRESS = 'design_in_progress'
    STATUS_DESIGN_COMPLETED = 'design_completed'
    STATUS_DESIGN_REJECTED = 'design_rejected'
    STATUS_APPROVED_FOR_PRINTING = 'approved_for_printing'
    STATUS_PRINTING_QUEUED = 'printing_queued'
    STATUS_PRINTING = 'printing'
    STATUS_POLISHING = 'polishing'
    STATUS_READY_FOR_PICKUP = 'ready_for_pickup'
    STATUS_OUT_FOR_DELIVERY = 'out_for_delivery'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ASSIGNED_TO_DESIGNER, 'Assigned to Designer'),
        (STATUS_DESIGN_IN_PROGRESS, 'Design In Progress'),
        (STATUS_DESIGN_COMPLETED, 'Design Completed'),
        (STATUS_DESIGN_REJECTED, 'Design Rejected'),
        (STATUS_APPROVED_FOR_PRINTING, 'Approved for Printing'),
        (STATUS_PRINTING_QUEUED, 'Printing Queued'),
        (STATUS_PRINTING, 'Printing'),
        (STATUS_POLISHING, 'Polishing'),
        (STATUS_READY_FOR_PICKUP, 'Ready for Pickup'),
        (STATUS_OUT_FOR_DELIVERY, 'Out for Delivery'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]
    
    # Company and User
    company = models.ForeignKey(
        'companies.Company',
        on_delete=models.CASCADE,
        related_name='orders'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    
    # Order Number
    order_number = models.CharField(max_length=20, unique=True, blank=True)
    
    # Assignments
    assigned_designer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='design_assignments'
    )
    assigned_printer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='print_assignments'
    )
    
    # Pricing
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    delivery_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Design
    needs_design = models.BooleanField(default=False)
    design_file = models.FileField(upload_to='designs/', blank=True, null=True)
    design_description = models.TextField(blank=True)
    design_notes = models.TextField(blank=True)
    design_revisions = models.PositiveIntegerField(default=0)
    max_revisions = models.PositiveIntegerField(default=3)
    client_files = models.JSONField(default=list, blank=True)
    
    # Status
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    rejection_reason = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    # Priority
    PRIORITY_LOW = 'low'
    PRIORITY_NORMAL = 'normal'
    PRIORITY_HIGH = 'high'
    PRIORITY_URGENT = 'urgent'
    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_NORMAL, 'Normal'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_URGENT, 'Urgent'),
    ]
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default=PRIORITY_NORMAL)
    
    # Notes
    description = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    design_started_at = models.DateTimeField(null=True, blank=True)
    design_completed_at = models.DateTimeField(null=True, blank=True)
    printing_started_at = models.DateTimeField(null=True, blank=True)
    printing_completed_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    estimated_completion = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.order_number
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = generate_order_number()
        super().save(*args, **kwargs)
    
    @property
    def can_assign_designer(self):
        return self.needs_design and self.status == self.STATUS_PENDING and not self.assigned_designer
    
    @property
    def can_start_design(self):
        return self.status == self.STATUS_ASSIGNED_TO_DESIGNER
    
    @property
    def can_submit_design(self):
        return self.status == self.STATUS_DESIGN_IN_PROGRESS
    
    @property
    def can_approve_design(self):
        return self.status == self.STATUS_DESIGN_COMPLETED
    
    @property
    def can_start_printing(self):
        return self.status in [self.STATUS_APPROVED_FOR_PRINTING, self.STATUS_PRINTING_QUEUED]
    
    def update_status(self, new_status, user=None, note=''):
        """Update order status and create history record."""
        old_status = self.status
        self.status = new_status
        
        if new_status == self.STATUS_DESIGN_IN_PROGRESS:
            self.design_started_at = timezone.now()
        elif new_status == self.STATUS_DESIGN_COMPLETED:
            self.design_completed_at = timezone.now()
        elif new_status == self.STATUS_PRINTING:
            self.printing_started_at = timezone.now()
        elif new_status == self.STATUS_POLISHING:
            self.printing_completed_at = timezone.now()
        elif new_status == self.STATUS_COMPLETED:
            self.completed_at = timezone.now()
        
        self.save()
        
        OrderStatusHistory.objects.create(
            order=self,
            old_status=old_status,
            new_status=new_status,
            changed_by=user,
            note=note
        )


class OrderItem(models.Model):
    """Items in an order."""
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    specifications = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['id']
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def save(self, *args, **kwargs):
        self.unit_price = self.product.get_price_for_quantity(self.quantity)
        self.subtotal = self.unit_price * self.quantity
        super().save(*args, **kwargs)
        
        # Update order total
        self.order.subtotal = sum(item.subtotal for item in self.order.items.all())
        self.order.total_price = self.order.subtotal + self.order.tax + self.order.delivery_fee - self.order.discount
        self.order.save()

class OrderItemFieldValue(models.Model):
    """Values for custom product fields."""
    
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='field_values')
    field = models.ForeignKey('products.ProductField', on_delete=models.CASCADE)
    value = models.TextField()
    file_url = models.URLField(blank=True)
    
    class Meta:
        unique_together = ['order_item', 'field']
    
    def __str__(self):
        return f"{self.field.name}: {self.value[:50]}"


class OrderStatusHistory(models.Model):
    """Track all status changes for an order."""
    
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=30)
    new_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Order Status History'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order.order_number}: {self.old_status} → {self.new_status}"

class PrintJob(models.Model):
    """Printer's job tracking with detailed status."""
    STATUS_QUEUED = 'queued'
    STATUS_IN_PRINTING = 'in_printing'
    STATUS_PAUSED = 'paused'
    STATUS_POLISHING = 'polishing'
    STATUS_COMPLETED = 'completed'
    
    STATUS_CHOICES = [
        (STATUS_QUEUED, 'Queued'),
        (STATUS_IN_PRINTING, 'In Printing'),
        (STATUS_PAUSED, 'Paused'),
        (STATUS_POLISHING, 'Polishing'),
        (STATUS_COMPLETED, 'Completed'),
    ]
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='print_job')
    assigned_printer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='print_jobs'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    print_quantity = models.PositiveIntegerField(default=1)
    paper_type = models.CharField(max_length=100, blank=True)
    print_color = models.CharField(max_length=50, blank=True)
    finish_type = models.CharField(max_length=50, blank=True)
    progress_percentage = models.PositiveIntegerField(default=0)
    print_notes = models.TextField(blank=True)
    issues = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    estimated_completion = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Print Job #{self.id} - {self.order.order_number}"
    
    def start(self):
        self.status = self.STATUS_IN_PRINTING
        self.started_at = timezone.now()
        self.save()
        self.order.update_status(Order.STATUS_PRINTING, note="Printing started")
    
    def move_to_polishing(self):
        self.status = self.STATUS_POLISHING
        self.save()
        self.order.update_status(Order.STATUS_POLISHING, note="Moved to polishing")
    
    def complete(self):
        self.status = self.STATUS_COMPLETED
        self.completed_at = timezone.now()
        self.progress_percentage = 100
        self.save()
        self.order.update_status(Order.STATUS_READY_FOR_PICKUP, note="Printing completed")

class Transportation(models.Model):
    """Transportation/Delivery information for orders."""
    TRANSPORT_PICKUP = 'pickup'
    TRANSPORT_DELIVERY = 'delivery'
    TRANSPORT_UBER = 'uber'
    
    TRANSPORT_CHOICES = [
        (TRANSPORT_PICKUP, 'Client Pickup'),
        (TRANSPORT_DELIVERY, 'Company Delivery'),
        (TRANSPORT_UBER, 'Uber/Third-party'),
    ]
    
    STATUS_PENDING = 'pending'
    STATUS_SCHEDULED = 'scheduled'
    STATUS_IN_TRANSIT = 'in_transit'
    STATUS_DELIVERED = 'delivered'
    STATUS_FAILED = 'failed'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_IN_TRANSIT, 'In Transit'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_FAILED, 'Failed'),
    ]
    
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='transportation')
    
    transport_type = models.CharField(max_length=20, choices=TRANSPORT_CHOICES, default=TRANSPORT_PICKUP)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    
    delivery_address = models.TextField(blank=True)
    delivery_city = models.CharField(max_length=100, blank=True)
    delivery_phone = models.CharField(max_length=20, blank=True)
    delivery_instructions = models.TextField(blank=True)
    
    pickup_location = models.TextField(blank=True)
    pickup_scheduled_time = models.DateTimeField(null=True, blank=True)
    
    delivery_scheduled_time = models.DateTimeField(null=True, blank=True)
    estimated_arrival = models.DateTimeField(null=True, blank=True)
    actual_delivery_time = models.DateTimeField(null=True, blank=True)
    
    tracking_number = models.CharField(max_length=100, blank=True)
    tracking_url = models.URLField(blank=True)
    driver_name = models.CharField(max_length=100, blank=True)
    driver_phone = models.CharField(max_length=20, blank=True)
    
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.get_transport_type_display()}"
    
    @property
    def is_pickup(self):
        return self.transport_type == self.TRANSPORT_PICKUP
    
    @property
    def is_delivery(self):
        return self.transport_type in [self.TRANSPORT_DELIVERY, self.TRANSPORT_UBER]
