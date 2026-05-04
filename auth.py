import os
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from database import create_reset_token


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def generate_reset_token(user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    create_reset_token(user_id, token, expires_at)
    return token


def send_reset_email(to_email: str, token: str, app_url: str = "https://stratedge-7dguhxuprxzzgjwjflr23j.streamlit.app"):
    api_key = os.getenv("SENDGRID_API_KEY")
    sender = os.getenv("SENDGRID_EMAIL", "simonwoodbury35@gmail.com")
    reset_link = f"{app_url}?reset_token={token}"
    message = Mail(
        from_email=sender,
        to_emails=to_email,
        subject="StratEdge — Password Reset",
        html_content=f"""
        <p>You requested a password reset for your StratEdge account.</p>
        <p><a href="{reset_link}">Click here to reset your password</a></p>
        <p>This link expires in 1 hour. If you didn't request this, you can safely ignore this email.</p>
        """,
    )
    sg = SendGridAPIClient(api_key)
    sg.send(message)
