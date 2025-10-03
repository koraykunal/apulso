from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import EmailVerificationToken
import logging
import resend

logger = logging.getLogger(__name__)

# Configure Resend API key
resend.api_key = settings.RESEND_API_KEY if hasattr(settings, 'RESEND_API_KEY') else None


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

    try:
        params = {
            "from": f"Apulso <{settings.DEFAULT_FROM_EMAIL}>",
            "to": [user.email],
            "subject": "Verify Your Email - Apulso",
            "html": html_message,
        }
        resend.Emails.send(params)
        logger.info(f"Verification email sent to {user.email} via Resend")
    except Exception as e:
        logger.error(f"Failed to send verification email via Resend: {str(e)}")
        raise

    return token


def send_password_reset_email(user, reset_url):
    context = {
        'user': user,
        'reset_url': reset_url,
        'site_name': 'Apulso',
    }

    html_message = render_to_string('emails/password_reset.html', context)

    try:
        params = {
            "from": f"Apulso <{settings.DEFAULT_FROM_EMAIL}>",
            "to": [user.email],
            "subject": "Şifre Sıfırlama - Apulso",
            "html": html_message,
        }
        resend.Emails.send(params)
        logger.info(f"Password reset email sent to {user.email} via Resend")
    except Exception as e:
        logger.error(f"Failed to send password reset email via Resend: {str(e)}")
        raise


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

    try:
        params = {
            "from": f"Apulso <{settings.DEFAULT_FROM_EMAIL}>",
            "to": [new_email],
            "subject": "Verify Your New Email - Apulso",
            "html": html_message,
        }
        resend.Emails.send(params)
        logger.info(f"Email change verification sent to {new_email} via Resend")
    except Exception as e:
        logger.error(f"Failed to send email change verification via Resend: {str(e)}")
        raise
