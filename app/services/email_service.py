"""Email service stub — logs emails instead of sending (SMTP not configured)."""
import logging

logger = logging.getLogger(__name__)


def send_password_reset_email(email: str, reset_token: str) -> None:
    """
    Send a password-reset email.

    Currently this only logs the token; wire up an SMTP/SendGrid integration here.
    """
    logger.info(
        "PASSWORD RESET REQUESTED | email=%s | token=%s",
        email,
        reset_token,
    )


def send_welcome_email(email: str, full_name: str) -> None:
    """Send a welcome email to a new user."""
    logger.info("WELCOME EMAIL | email=%s | name=%s", email, full_name)
