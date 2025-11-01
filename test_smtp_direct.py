#!/usr/bin/env python
"""
Direct SMTP test without Django
"""
import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email configuration
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = 'smashking753@gmail.com'
EMAIL_PASSWORD = 'endydpizftzksdvo'

print("=" * 50)
print("DIRECT SMTP CONNECTION TEST")
print("=" * 50)
print(f"Host: {EMAIL_HOST}")
print(f"Port: {EMAIL_PORT}")
print(f"User: {EMAIL_USER}")
print(f"Password: {'*' * len(EMAIL_PASSWORD)}")
print("=" * 50)

# Test 1: Check if we can resolve the host
print("\n[1] Testing DNS resolution...")
try:
    ip = socket.gethostbyname(EMAIL_HOST)
    print(f"✓ DNS resolution successful: {EMAIL_HOST} -> {ip}")
except socket.gaierror as e:
    print(f"✗ DNS resolution failed: {e}")
    exit(1)

# Test 2: Check if we can connect to the port
print(f"\n[2] Testing TCP connection to {EMAIL_HOST}:{EMAIL_PORT}...")
try:
    socket.setdefaulttimeout(10)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((EMAIL_HOST, EMAIL_PORT))
    print(f"✓ TCP connection successful")
    sock.close()
except socket.error as e:
    print(f"✗ TCP connection failed: {e}")
    print("\nPossible issues:")
    print("- Firewall blocking port 587")
    print("- Network/ISP blocking SMTP")
    print("- WSL networking issues")
    exit(1)

# Test 3: Try to send email via SMTP
print(f"\n[3] Testing SMTP authentication and email sending...")
try:
    # Create message
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER
    msg['Subject'] = 'Test Email from Nexpress'
    body = 'This is a test email to verify SMTP configuration.'
    msg.attach(MIMEText(body, 'plain'))

    # Connect and send
    print("Connecting to SMTP server...")
    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=30)
    server.set_debuglevel(0)  # Set to 1 for verbose output

    print("Starting TLS...")
    server.starttls()

    print("Authenticating...")
    server.login(EMAIL_USER, EMAIL_PASSWORD)

    print("Sending email...")
    server.send_message(msg)
    server.quit()

    print(f"✓ Email sent successfully to {EMAIL_USER}!")
    print("\nCheck your inbox (and spam folder).")

except smtplib.SMTPAuthenticationError as e:
    print(f"✗ Authentication failed: {e}")
    print("\nPossible issues:")
    print("- Incorrect app password")
    print("- 2-Step Verification not enabled")
    print("- App password has spaces or typos")
    print("\nYour app password should be: endy dpiz ftzk sdvo (with spaces)")
    print("In .env it should be: endydpizftzksdvo (without spaces)")

except smtplib.SMTPException as e:
    print(f"✗ SMTP error: {e}")

except socket.timeout:
    print(f"✗ Connection timed out after 30 seconds")
    print("\nPossible issues:")
    print("- Firewall blocking connection")
    print("- Network issues")
    print("- ISP blocking SMTP ports")

except Exception as e:
    print(f"✗ Unexpected error: {type(e).__name__}: {e}")

print("\n" + "=" * 50)
