from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import EmailVerificationToken
import logging

logger = logging.getLogger(__name__)


def send_verification_email(user, request=None):
    token = EmailVerificationToken.objects.create(user=user)

    frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:3000'
    verification_url = f"{frontend_url}/auth/verify-email?token={token.token}"

    context = {
        'user': user,
        'verification_url': verification_url,
        'site_name': 'Apulso',
    }

    html_message = render_to_string('emails/verify_email.html', context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject='Verify Your Email - Apulso',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )

    return token


def send_password_reset_email(user, reset_url):
    context = {
        'user': user,
        'reset_url': reset_url,
        'site_name': 'Apulso',
    }

    html_message = render_to_string('emails/password_reset.html', context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject='Şifre Sıfırlama - Apulso',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_message,
        fail_silently=False,
    )


def send_email_change_verification(user, new_email, token):
    from .models import EmailChangeRequest

    frontend_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'http://localhost:3000'
    verification_url = f"{frontend_url}/auth/verify-email-change?token={token}"

    context = {
        'user': user,
        'new_email': new_email,
        'verification_url': verification_url,
        'site_name': 'Apulso',
    }

    html_message = render_to_string('emails/email_change.html', context)
    plain_message = strip_tags(html_message)

    send_mail(
        subject='Verify Your New Email - Apulso',
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[new_email],
        html_message=html_message,
        fail_silently=False,
    )
