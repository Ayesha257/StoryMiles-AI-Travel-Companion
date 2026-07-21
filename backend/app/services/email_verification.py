from __future__ import annotations

import asyncio
import hashlib
import hmac
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from email.utils import formataddr

from app.auth.security import hash_password
from app.core.config import settings
from app.core.exceptions import EmailDeliveryError, RateLimitError, VerificationError
from app.models.user import User
from app.repositories.user import UserRepository


class EmailVerificationService:
    MAX_ATTEMPTS = 5

    def __init__(self, users: UserRepository) -> None:
        self.users = users

    async def send_code(
        self,
        user: User,
        *,
        purpose: str = "email_verification",
        enforce_cooldown: bool = False,
    ) -> None:
        now = datetime.now(timezone.utc)
        if (
            enforce_cooldown
            and user.verification_code_sent_at
            and now - user.verification_code_sent_at
            < timedelta(seconds=settings.verification_resend_cooldown_seconds)
        ):
            remaining = settings.verification_resend_cooldown_seconds - int(
                (now - user.verification_code_sent_at).total_seconds()
            )
            raise RateLimitError(
                f"Please wait {max(remaining, 1)} seconds before requesting another code",
                retry_after=max(remaining, 1),
            )

        code = f"{secrets.randbelow(1_000_000):06d}"
        await self._deliver(user.email, code, purpose)
        await self.users.update(
            user,
            verification_code_hash=self._hash_code(user, code),
            verification_code_purpose=purpose,
            verification_code_expires_at=now
            + timedelta(minutes=settings.verification_code_expire_minutes),
            verification_code_sent_at=now,
            verification_attempts=0,
        )

    async def verify(self, email: str, code: str) -> User:
        user = await self.users.get_by_email(email)
        if user is None:
            raise VerificationError("Invalid or expired verification code")
        if user.is_verified:
            return user

        await self._validate_code(user, code, "email_verification")

        user.is_verified = True
        self._clear_code(user)
        await self.users.session.flush()
        await self.users.session.refresh(user)
        return user

    async def resend(self, email: str) -> None:
        user = await self.users.get_by_email(email)
        # Keep the response non-enumerating for unknown/already verified accounts.
        if user is None or user.is_verified:
            return
        await self.send_code(user, purpose="email_verification", enforce_cooldown=True)

    async def request_password_reset(self, email: str) -> None:
        user = await self.users.get_by_email(email)
        # Always return the same API message so account existence is not exposed.
        if user is None or not user.is_active or not user.is_verified:
            return
        await self.send_code(user, purpose="password_reset", enforce_cooldown=True)

    async def reset_password(self, email: str, code: str, new_password: str) -> None:
        user = await self.users.get_by_email(email)
        if user is None:
            raise VerificationError("Invalid or expired reset code")
        await self._validate_code(user, code, "password_reset")
        user.password_hash = hash_password(new_password)
        self._clear_code(user)
        await self.users.session.flush()

    async def _validate_code(self, user: User, code: str, purpose: str) -> None:
        now = datetime.now(timezone.utc)
        if (
            not user.verification_code_hash
            or not user.verification_code_expires_at
            or user.verification_code_purpose != purpose
        ):
            raise VerificationError("Invalid or expired code")
        if user.verification_code_expires_at < now:
            raise VerificationError("This code has expired. Request a new one")
        if user.verification_attempts >= self.MAX_ATTEMPTS:
            raise VerificationError("Too many attempts. Request a new code")
        if not hmac.compare_digest(user.verification_code_hash, self._hash_code(user, code)):
            await self.users.update(user, verification_attempts=user.verification_attempts + 1)
            await self.users.session.commit()
            raise VerificationError("The code is incorrect")

    @staticmethod
    def _clear_code(user: User) -> None:
        user.verification_code_hash = None
        user.verification_code_purpose = None
        user.verification_code_expires_at = None
        user.verification_code_sent_at = None
        user.verification_attempts = 0

    @staticmethod
    def _hash_code(user: User, code: str) -> str:
        payload = f"{user.id}:{code}".encode()
        return hmac.new(settings.jwt_secret_key.encode(), payload, hashlib.sha256).hexdigest()

    async def _deliver(self, recipient: str, code: str, purpose: str) -> None:
        if not settings.smtp_username or not settings.smtp_password:
            raise EmailDeliveryError(
                "Email delivery is not configured. Add SMTP_USERNAME and SMTP_PASSWORD to backend/.env"
            )
        sender = settings.smtp_from_email or settings.smtp_username
        is_reset = purpose == "password_reset"
        message = EmailMessage()
        message["Subject"] = (
            f"{code} is your StoryMiles password reset code"
            if is_reset
            else f"{code} is your StoryMiles verification code"
        )
        message["From"] = formataddr((settings.smtp_from_name, sender))
        message["To"] = recipient
        message.set_content(
            f"Your StoryMiles {'password reset' if is_reset else 'verification'} code is {code}.\n"
            f"It expires in {settings.verification_code_expire_minutes} minutes.\n\n"
            f"If you did not {'request a password reset' if is_reset else 'create this account'}, "
            "you can ignore this email."
        )
        message.add_alternative(self._html(code, is_reset), subtype="html")

        try:
            await asyncio.to_thread(self._send_smtp, message)
        except (OSError, smtplib.SMTPException) as exc:
            raise EmailDeliveryError("We could not send the verification email. Please try again") from exc

    @staticmethod
    def _send_smtp(message: EmailMessage) -> None:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)

    @staticmethod
    def _html(code: str, is_reset: bool) -> str:
        heading = "Reset your password" if is_reset else "Verify your email"
        description = (
            "Enter this code in StoryMiles to choose a new password."
            if is_reset
            else "Enter this code to finish creating your travel account."
        )
        return f"""
        <!doctype html>
        <html>
          <body style="margin:0;background:#f6f0e5;font-family:Arial,sans-serif;color:#29251f">
            <div style="max-width:560px;margin:32px auto;padding:0 18px">
              <div style="background:#fff;border:1px solid #e4dac8;border-radius:24px;
                          padding:40px;text-align:center;box-shadow:0 16px 40px #5b463218">
                <div style="font-size:12px;letter-spacing:3px;text-transform:uppercase;
                            color:#c95f3f;font-weight:700">StoryMiles</div>
                <h1 style="font-family:Georgia,serif;font-size:30px;margin:18px 0 8px">
                  {heading}
                </h1>
                <p style="color:#6d655a;line-height:1.6;margin:0 0 26px">
                  {description}
                </p>
                <div style="display:inline-block;background:#29251f;color:#fff;border-radius:14px;
                            padding:17px 26px;font-size:30px;letter-spacing:9px;font-weight:700">
                  {code}
                </div>
                <p style="font-size:13px;color:#8a8175;margin:26px 0 0">
                  This code expires in {settings.verification_code_expire_minutes} minutes.
                </p>
              </div>
            </div>
          </body>
        </html>
        """
