"""
Custom email backend with extended timeout for WSL
"""
from django.core.mail.backends.smtp import EmailBackend as DjangoEmailBackend
import smtplib


class ExtendedTimeoutEmailBackend(DjangoEmailBackend):
    """
    Custom email backend that sets longer timeout for WSL compatibility
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Force timeout to be at least 60 seconds for WSL
        if not self.timeout or self.timeout < 60:
            self.timeout = 60

    def open(self):
        """
        Ensure we have a connection to the email server with extended timeout.
        """
        if self.connection:
            return False

        try:
            if self.use_ssl:
                self.connection = smtplib.SMTP_SSL(
                    self.host,
                    self.port,
                    timeout=self.timeout
                )
            else:
                self.connection = smtplib.SMTP(
                    self.host,
                    self.port,
                    timeout=self.timeout
                )

            if self.use_tls:
                self.connection.ehlo()
                self.connection.starttls()
                self.connection.ehlo()

            if self.username and self.password:
                self.connection.login(self.username, self.password)

            return True
        except (smtplib.SMTPException, OSError):
            if self.connection:
                self.connection.quit()
                self.connection = None
            raise
