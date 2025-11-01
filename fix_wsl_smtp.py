#!/usr/bin/env python
"""
Try different approaches to make Gmail SMTP work from WSL
"""
import smtplib
import socket
import ssl
from email.mime.text import MIMEText

EMAIL_USER = 'smashking753@gmail.com'
EMAIL_PASSWORD = 'endydpizftzksdvo'

print("=" * 60)
print("TESTING DIFFERENT SMTP APPROACHES FOR WSL")
print("=" * 60)

# Approach 1: Standard SMTP with longer timeout
print("\n[Approach 1] Standard SMTP with TLS (60s timeout)...")
try:
    msg = MIMEText('Test email - Approach 1')
    msg['Subject'] = 'Test Email - TLS 60s timeout'
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER

    server = smtplib.SMTP('smtp.gmail.com', 587, timeout=60)
    server.set_debuglevel(0)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login(EMAIL_USER, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()
    print("✓ SUCCESS! Standard SMTP with TLS works with 60s timeout")
    print("SOLUTION: Increase EMAIL_TIMEOUT in Django settings")
    exit(0)
except Exception as e:
    print(f"✗ Failed: {type(e).__name__}: {e}")

# Approach 2: SMTP with SSL (port 465)
print("\n[Approach 2] SMTP_SSL (port 465)...")
try:
    msg = MIMEText('Test email - Approach 2')
    msg['Subject'] = 'Test Email - SSL port 465'
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER

    context = ssl.create_default_context()
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=60, context=context)
    server.set_debuglevel(0)
    server.login(EMAIL_USER, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()
    print("✓ SUCCESS! SMTP_SSL on port 465 works")
    print("SOLUTION: Change Django to use port 465 with SSL")
    exit(0)
except Exception as e:
    print(f"✗ Failed: {type(e).__name__}: {e}")

# Approach 3: Try with custom SSL context
print("\n[Approach 3] SMTP with custom SSL context...")
try:
    msg = MIMEText('Test email - Approach 3')
    msg['Subject'] = 'Test Email - Custom SSL context'
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER

    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    server = smtplib.SMTP('smtp.gmail.com', 587, timeout=60)
    server.set_debuglevel(0)
    server.ehlo()
    server.starttls(context=context)
    server.ehlo()
    server.login(EMAIL_USER, EMAIL_PASSWORD)
    server.send_message(msg)
    server.quit()
    print("✓ SUCCESS! Works with relaxed SSL verification")
    print("SOLUTION: Use custom SSL context in Django")
    exit(0)
except Exception as e:
    print(f"✗ Failed: {type(e).__name__}: {e}")

# Approach 4: Direct socket connection test
print("\n[Approach 4] Testing raw socket connection...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(60)
    sock.connect(('smtp.gmail.com', 587))
    print("✓ Raw socket connection works")
    sock.close()
except Exception as e:
    print(f"✗ Raw socket failed: {e}")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("All SMTP approaches failed from WSL.")
print("\nRECOMMENDED SOLUTIONS:")
print("1. Run Django from Windows Command Prompt (not WSL)")
print("2. Deploy to a real Linux server (not WSL)")
print("3. Use a different email service (SendGrid, Mailgun, etc.)")
print("=" * 60)
