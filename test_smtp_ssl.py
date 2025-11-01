#!/usr/bin/env python
"""
Test SMTP with SSL (port 465) instead of TLS (port 587)
"""
import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email configuration - trying port 465 with SSL
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 465  # SSL port instead of TLS
EMAIL_USER = 'smashking753@gmail.com'
EMAIL_PASSWORD = 'endydpizftzksdvo'

print("=" * 50)
print("SMTP SSL TEST (Port 465)")
print("=" * 50)
print(f"Host: {EMAIL_HOST}")
print(f"Port: {EMAIL_PORT}")
print(f"User: {EMAIL_USER}")
print("=" * 50)

try:
    # Create message
    msg = MIMEMultipart()
    msg['From'] = EMAIL_USER
    msg['To'] = EMAIL_USER
    msg['Subject'] = 'Test Email from Nexpress (SSL)'
    body = 'This is a test email using SSL on port 465.'
    msg.attach(MIMEText(body, 'plain'))

    print("\nConnecting to SMTP server with SSL...")
    # Use SMTP_SSL instead of SMTP + starttls
    server = smtplib.SMTP_SSL(EMAIL_HOST, EMAIL_PORT, timeout=30)
    server.set_debuglevel(0)

    print("Authenticating...")
    server.login(EMAIL_USER, EMAIL_PASSWORD)

    print("Sending email...")
    server.send_message(msg)
    server.quit()

    print(f"\n✓ Email sent successfully to {EMAIL_USER}!")
    print("Check your inbox (and spam folder).")
    print("\nSolution: Use port 465 with SSL instead of port 587 with TLS")

except smtplib.SMTPAuthenticationError as e:
    print(f"\n✗ Authentication failed: {e}")
    print("\nCheck your app password")

except socket.timeout:
    print(f"\n✗ Connection timed out")
    print("Both port 587 (TLS) and 465 (SSL) failed.")
    print("\nTry these solutions:")
    print("1. Check Windows Defender Firewall")
    print("2. Check antivirus blocking SMTP")
    print("3. Try from outside WSL (Windows native Python)")

except Exception as e:
    print(f"\n✗ Error: {type(e).__name__}: {e}")

print("\n" + "=" * 50)
