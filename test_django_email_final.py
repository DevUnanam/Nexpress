#!/usr/bin/env python
"""
Final test of Django email configuration with proper timeout
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedex_clone.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("=" * 60)
print("DJANGO EMAIL TEST WITH 60-SECOND TIMEOUT")
print("=" * 60)
print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"EMAIL_TIMEOUT: {settings.EMAIL_TIMEOUT}")
print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
print("=" * 60)

recipient = settings.EMAIL_HOST_USER
print(f"\nSending test email to: {recipient}")
print("This may take up to 60 seconds...")

try:
    result = send_mail(
        subject='✓ Gmail SMTP Working from Nexpress!',
        message='Congratulations! Your Gmail SMTP configuration is working correctly from WSL.\n\nEmail verification is now fully functional.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
        fail_silently=False,
    )
    print(f"\n✓✓✓ SUCCESS! Email sent successfully!")
    print(f"Result: {result} email(s) sent")
    print(f"\nCheck {recipient} inbox (or spam folder)")
    print("\nGmail SMTP is now working for email verification!")
except Exception as e:
    print(f"\n✗ Error: {type(e).__name__}")
    print(f"Details: {str(e)}")
    print("\nIf this still fails, the 60s timeout may not be enough.")
    print("You can increase it further in settings.py (try 90 or 120)")

print("=" * 60)
