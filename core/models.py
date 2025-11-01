from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import hashlib
import uuid

# Create your models here.

class UserProfile(AbstractUser):
    """
    Custom user model extending AbstractUser with role-based access
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('shipper', 'Shipper'),
        ('courier', 'Courier'),
        ('recipient', 'Recipient'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='recipient',
        help_text='User role in the system'
    )
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'


class Shipment(models.Model):
    """
    Shipment model for tracking packages
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('picked_up', 'Picked Up'),
        ('in_transit', 'In Transit'),
        ('hold', 'Hold'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned'),
    ]

    shipper = models.ForeignKey(
        'UserProfile',
        on_delete=models.CASCADE,
        related_name='shipments_sent',
        help_text='User who is sending the package'
    )
    recipient_name = models.CharField(max_length=255)
    recipient_phone = models.CharField(max_length=20, blank=True)
    recipient_email = models.EmailField(blank=True)

    pickup_address = models.TextField(help_text='Address to pick up the package')
    delivery_address = models.TextField(help_text='Address to deliver the package')

    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Weight in kilograms'
    )

    tracking_number = models.CharField(
        max_length=20,
        unique=True,
        editable=False,
        help_text='Unique tracking number for this shipment'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Current status of the shipment'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    courier = models.ForeignKey(
        'UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shipments_assigned',
        help_text='Courier assigned to this shipment'
    )

    notes = models.TextField(blank=True, help_text='Additional notes about the shipment')

    hold_reason = models.TextField(
        blank=True,
        null=True,
        help_text='Reason for hold (e.g., customs clearance, regulatory issues)'
    )

    previous_status = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text='Previous status before current status'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Shipment'
        verbose_name_plural = 'Shipments'

    def __str__(self):
        return f"{self.tracking_number} - {self.get_status_display()}"

    def save(self, *args, **kwargs):
        # Generate tracking number if new shipment
        if not self.tracking_number:
            self.tracking_number = self.generate_tracking_number()
        else:
            # Check if status is being changed to 'returned'
            if self.pk:  # Only check for existing shipments
                try:
                    old_shipment = Shipment.objects.get(pk=self.pk)
                    # If status changed to 'returned', generate new tracking number
                    if old_shipment.status != 'returned' and self.status == 'returned':
                        self.tracking_number = self.generate_tracking_number()
                except Shipment.DoesNotExist:
                    pass

        super().save(*args, **kwargs)

    def generate_tracking_number(self):
        """
        Generate a unique tracking number using FD prefix + timestamp hash
        Format: FD-XXXXXXXXXX (12 characters total)
        """
        timestamp = timezone.now().timestamp()
        # Create a hash from timestamp and a random component
        hash_input = f"{timestamp}{id(self)}"
        hash_object = hashlib.sha256(hash_input.encode())
        hash_hex = hash_object.hexdigest()[:10].upper()

        tracking_code = f"FD{hash_hex}"

        # Ensure uniqueness
        while Shipment.objects.filter(tracking_number=tracking_code).exists():
            hash_input = f"{timestamp}{id(self)}{tracking_code}"
            hash_object = hashlib.sha256(hash_input.encode())
            hash_hex = hash_object.hexdigest()[:10].upper()
            tracking_code = f"FD{hash_hex}"

        return tracking_code

    def get_status_badge_class(self):
        """
        Return Tailwind CSS classes for status badge
        Pending → gray
        Accepted → light blue
        Picked Up → medium blue
        In Transit → deep blue (royal blue)
        Hold → yellow/orange (warning)
        Delivered → green
        Returned → red
        """
        status_classes = {
            'pending': 'bg-gray-100 text-gray-800',
            'accepted': 'bg-blue-100 text-blue-800',
            'picked_up': 'bg-blue-200 text-blue-900',
            'in_transit': 'bg-gradient-to-br from-green-500 to-emerald-700 text-white',
            'hold': 'bg-yellow-100 text-yellow-800 border border-yellow-300',
            'delivered': 'bg-green-100 text-green-800',
            'returned': 'bg-red-100 text-red-800 border border-red-300',
        }
        return status_classes.get(self.status, 'bg-gray-100 text-gray-800')

    def get_status_color(self):
        """
        Return color code for status visualization
        """
        status_colors = {
            'pending': 'gray',
            'accepted': 'blue',
            'picked_up': 'blue',
            'in_transit': 'primary',
            'hold': 'yellow',
            'delivered': 'green',
            'returned': 'red',
        }
        return status_colors.get(self.status, 'gray')

    def can_update_status(self, user):
        """
        Check if user can update the shipment status
        Admin can update any status
        Courier can update if assigned to them
        """
        if user.is_staff or user.role == 'admin':
            return True
        if user.role == 'courier' and self.courier == user:
            return True
        return False

    def get_next_statuses(self, user):
        """
        Get allowed statuses based on user role
        Admins can change to any status (including backwards)
        Couriers can only move forward
        """
        if not self.can_update_status(user):
            return []

        # Admin can change to any status
        if user.is_staff or user.role == 'admin':
            # Return all statuses except the current one
            return [status for status, _ in self.STATUS_CHOICES if status != self.status]

        # Courier can only move forward in the flow
        status_flow = {
            'pending': ['accepted'],
            'accepted': ['picked_up', 'hold'],
            'picked_up': ['in_transit', 'hold', 'returned'],
            'in_transit': ['hold', 'delivered', 'returned'],
            'hold': ['picked_up', 'in_transit', 'delivered', 'returned'],
            'delivered': [],
            'returned': ['pending'],  # Returned packages restart the flow
        }
        return status_flow.get(self.status, [])


class ShipmentStatusNote(models.Model):
    """
    Model to track status update notes/history
    Each time a status is updated, admin can add a note explaining the status
    """
    shipment = models.ForeignKey(
        'Shipment',
        on_delete=models.CASCADE,
        related_name='status_notes',
        help_text='Shipment this note belongs to'
    )
    status = models.CharField(
        max_length=20,
        choices=Shipment.STATUS_CHOICES,
        help_text='Status at the time of this note'
    )
    note = models.TextField(
        help_text='Admin note describing the current status or update'
    )
    created_by = models.ForeignKey(
        'UserProfile',
        on_delete=models.SET_NULL,
        null=True,
        related_name='status_notes_created',
        help_text='Admin who created this note'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When this note was created'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Shipment Status Note'
        verbose_name_plural = 'Shipment Status Notes'

    def __str__(self):
        return f"{self.shipment.tracking_number} - {self.get_status_display()} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
