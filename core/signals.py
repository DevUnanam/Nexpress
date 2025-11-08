# core/signals.py
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Shipment

@receiver(pre_save, sender=Shipment)
def store_previous_status(sender, instance, **kwargs):
    """
    Save the old status before the shipment is saved,
    so we can compare in post_save.
    """
    if instance.pk:
        try:
            old_instance = Shipment.objects.get(pk=instance.pk)
            instance.previous_status = old_instance.status
        except Shipment.DoesNotExist:
            instance.previous_status = None


@receiver(post_save, sender=Shipment)
def send_status_update_email(sender, instance, created, **kwargs):
    """
    Send an email to recipient when shipment status changes.
    """
    if created:
        return  # No need to send email on creation

    old_status = instance.previous_status
    new_status = instance.status

    # Only send email if status changed and recipient_email exists
    if old_status != new_status and instance.recipient_email:
        subject = f"Update on your shipment ({instance.tracking_number})"
        message = (
            f"Hello {instance.recipient_name},\n\n"
            f"The status of your shipment with tracking number {instance.tracking_number} has been updated.\n\n"
            f"Previous status: {old_status or 'N/A'}\n"
            f"Current status: {new_status.replace('_', ' ').title()}\n\n"
            f"Pickup Address: {instance.pickup_address}\n"
            f"Delivery Address: {instance.delivery_address}\n\n"
            "Thank you for using Nexpress!"
        )

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [instance.recipient_email],
                fail_silently=False,  # show errors if any
            )
            print(f"✅ Email sent to {instance.recipient_email}")
        except Exception as e:
            import traceback
            print("❌ Failed to send shipment update email:", e)
            print(traceback.format_exc())
