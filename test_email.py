#!/usr/bin/env python
"""
Test script to verify email configuration
Run with: python test_email.py
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fedex_clone.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    """Test sending an email"""
    print("=" * 50)
    print("EMAIL CONFIGURATION TEST")
    print("=" * 50)
    print(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"EMAIL_HOST_PASSWORD: {'*' * len(settings.EMAIL_HOST_PASSWORD) if settings.EMAIL_HOST_PASSWORD else 'NOT SET'}")
    print(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print("=" * 50)

    test_email_address = input("Enter test email address (press Enter to use EMAIL_HOST_USER): ").strip()
    if not test_email_address:
        test_email_address = settings.EMAIL_HOST_USER

    print(f"\nSending test email to: {test_email_address}")

    try:
        result = send_mail(
            subject='Test Email from Nexpress',
            message='This is a test email to verify your email configuration is working correctly.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[test_email_address],
            fail_silently=False,
        )
        print(f"\n✓ Email sent successfully! (Result: {result})")
        print("Check your inbox (and spam folder) for the test email.")
        return True
    except Exception as e:
        print(f"\n✗ Error sending email: {type(e).__name__}")
        print(f"Error details: {str(e)}")
        print("\nCommon issues:")
        print("1. Check that 2-Step Verification is enabled on your Google account")
        print("2. Make sure you're using an App Password, not your regular Gmail password")
        print("3. Verify the app password has no spaces")
        print("4. Check that 'Less secure app access' is not required (use App Passwords instead)")
        return False

if __name__ == '__main__':
    test_email()
