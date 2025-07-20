from django.core.mail import send_mail
from django.core.mail import BadHeaderError
import os


def send_email_to_admin(subject: str, body: str) -> None:
    try:
        send_mail(
            subject,
            body,
            None,  # Default to DEFAULT_FROM_EMAIL
            [os.environ.get('ADMIN_EMAIL')]
        )
    except BadHeaderError as e:
        print('Error sending email:')
        print(e)
