from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile, Shipment


class UserRegistrationForm(UserCreationForm):
    """
    Registration form for frontend users (automatically assigned 'recipient' role)
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary',
            'placeholder': 'Email address'
        })
    )

    phone_number = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary',
            'placeholder': 'Phone number'
        })
    )

    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary',
            'placeholder': 'Address',
            'rows': 3
        })
    )

    class Meta:
        model = UserProfile
        fields = ['username', 'email', 'phone_number', 'address', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary',
            'placeholder': 'Username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary',
            'placeholder': 'Confirm password'
        })

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone_number = self.cleaned_data.get('phone_number', '')
        user.address = self.cleaned_data.get('address', '')
        # Role will be set in the view (defaults to 'recipient' for frontend signups)
        if commit:
            user.save()
        return user


class ShipmentForm(forms.ModelForm):
    """
    Form for creating new shipments
    """
    courier = forms.ModelChoiceField(
        queryset=UserProfile.objects.filter(role='courier'),
        required=False,
        empty_label="Assign courier later",
        widget=forms.Select(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary'
        }),
        help_text='Select a courier to assign to this shipment'
    )

    recipient_name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary',
            'placeholder': 'Recipient full name'
        })
    )

    recipient_phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary',
            'placeholder': 'Recipient phone number'
        })
    )

    recipient_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary',
            'placeholder': 'Recipient email address'
        })
    )

    pickup_address = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary',
            'placeholder': 'Enter pickup address',
            'rows': 3
        })
    )

    delivery_address = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary',
            'placeholder': 'Enter delivery address',
            'rows': 3
        })
    )

    weight = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        min_value=0.01,
        widget=forms.NumberInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary',
            'placeholder': 'Weight in kilograms',
            'step': '0.01'
        })
    )

    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary',
            'placeholder': 'Additional notes (optional)',
            'rows': 3
        })
    )

    class Meta:
        model = Shipment
        fields = [
            'courier',
            'recipient_name',
            'recipient_phone',
            'recipient_email',
            'pickup_address',
            'delivery_address',
            'weight',
            'notes'
        ]

    def clean_weight(self):
        weight = self.cleaned_data.get('weight')
        if weight and weight <= 0:
            raise forms.ValidationError('Weight must be greater than 0.')
        if weight and weight > 1000:
            raise forms.ValidationError('Weight cannot exceed 1000 kg. For larger shipments, please contact support.')
        return weight

    def clean_pickup_address(self):
        address = self.cleaned_data.get('pickup_address')
        if address and len(address.strip()) < 10:
            raise forms.ValidationError('Please provide a complete pickup address.')
        return address

    def clean_delivery_address(self):
        address = self.cleaned_data.get('delivery_address')
        if address and len(address.strip()) < 10:
            raise forms.ValidationError('Please provide a complete delivery address.')
        return address

class ContactForm(forms.Form):
    """Simple contact form for user inquiries"""
    name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary',
            'placeholder': 'Your full name'
        })
    )

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary',
            'placeholder': 'you@domain.com'
        })
    )

    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary',
            'placeholder': 'Optional phone number'
        })
    )

    message = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={
            'class': 'mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary',
            'placeholder': 'Write your message here',
            'rows': 6
        })
    )

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Please enter your name.')
        return name

    def clean_message(self):
        msg = self.cleaned_data.get('message', '').strip()
        if len(msg) < 10:
            raise forms.ValidationError('Please provide a more detailed message (at least 10 characters).')
        return msg
