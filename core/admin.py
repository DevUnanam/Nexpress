from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import UserProfile, Shipment, ShipmentStatusNote

# Register your models here.

@admin.register(UserProfile)
class UserProfileAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'first_name', 'last_name', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number', 'address')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number', 'address')}),
    )


class ShipmentStatusNoteInline(admin.TabularInline):
    """Inline for viewing and adding status notes"""
    model = ShipmentStatusNote
    extra = 1
    fields = ['status', 'note', 'created_by', 'created_at']
    readonly_fields = ['created_by', 'created_at']

    def save_formset(self, request, form, formset, change):
        """Automatically set created_by to current user for new notes"""
        instances = formset.save(commit=False)
        for instance in instances:
            if not instance.pk:  # New note
                instance.created_by = request.user
            instance.save()
        formset.save_m2m()


@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = [
        'tracking_number',
        'shipper',
        'recipient_name',
        'status',
        'courier',
        'weight',
        'created_at',
        'updated_at'
    ]
    list_filter = ['status', 'created_at', 'updated_at', 'courier']
    search_fields = [
        'tracking_number',
        'recipient_name',
        'shipper__username',
        'courier__username'
    ]
    readonly_fields = ['tracking_number', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    list_per_page = 25
    inlines = [ShipmentStatusNoteInline]

    fieldsets = (
        ('Tracking Information', {
            'fields': ('tracking_number', 'status', 'hold_reason')
        }),
        ('Shipper Information', {
            'fields': ('shipper',)
        }),
        ('Recipient Information', {
            'fields': ('recipient_name', 'recipient_phone', 'recipient_email')
        }),
        ('Addresses', {
            'fields': ('pickup_address', 'delivery_address')
        }),
        ('Package Details', {
            'fields': ('weight', 'notes')
        }),
        ('Assignment', {
            'fields': ('courier',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    class Media:
        js = ('admin/js/shipment_admin.js',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('shipper', 'courier')

    def save_formset(self, request, form, formset, change):
        """Save formset and set created_by for status notes"""
        if formset.model == ShipmentStatusNote:
            instances = formset.save(commit=False)
            for instance in instances:
                if not instance.pk:  # New note
                    instance.created_by = request.user
                instance.save()
            formset.save_m2m()
        else:
            formset.save()

    def save_model(self, request, obj, form, change):
        """Send email notification when status changes"""
        if change:
            # Get the original object from database
            try:
                original = Shipment.objects.get(pk=obj.pk)
                if original.status != obj.status:
                    # Status has changed - store previous status
                    obj.previous_status = original.status
                    # Send email notification
                    self.send_status_change_email(obj, original.status, obj.status)
            except Shipment.DoesNotExist:
                pass

        super().save_model(request, obj, form, change)

    def send_status_change_email(self, shipment, old_status, new_status):
        """Send email notification about status change"""
        from django.core.mail import send_mail
        from django.conf import settings

        # Prepare email recipients
        recipients = []

        # Add shipper email
        if shipment.shipper.email:
            recipients.append(shipment.shipper.email)

        # Add recipient email if provided
        if shipment.recipient_email:
            recipients.append(shipment.recipient_email)

        if not recipients:
            return

        # Prepare email content
        subject = f'Shipment Update - {shipment.tracking_number}'

        old_status_display = dict(Shipment.STATUS_CHOICES).get(old_status, old_status)
        new_status_display = dict(Shipment.STATUS_CHOICES).get(new_status, new_status)

        message = f'''
Hello,

Your shipment status has been updated:

Tracking Number: {shipment.tracking_number}
Previous Status: {old_status_display}
New Status: {new_status_display}
'''

        # Add hold reason if status is hold
        if new_status == 'hold' and shipment.hold_reason:
            message += f'\nReason for Hold: {shipment.hold_reason}\n'

        message += f'''
Package Details:
- From: {shipment.shipper.username}
- To: {shipment.recipient_name}
- Weight: {shipment.weight} kg

You can track your shipment at any time using your tracking number.

Thank you for using our service!

Best regards,
Nexpress Team
        '''

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@nexpress.com',
                recipients,
                fail_silently=True,
            )
        except Exception as e:
            print(f"Error sending status change email: {e}")
