from pydantic import EmailStr, Field

from app.schemas.common import Schema
from app.schemas.user import UserResponse


class RegisterRequest(Schema):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)


class LoginRequest(Schema):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(Schema):
    refresh_token: str = Field(min_length=1)


class TokenResponse(Schema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RegisterResponse(Schema):
    email: EmailStr
    message: str
    verification_required: bool = True


class VerifyEmailRequest(Schema):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ResendVerificationRequest(Schema):
    email: EmailStr


class ForgotPasswordRequest(Schema):
    email: EmailStr


class ResetPasswordRequest(Schema):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    new_password: str = Field(min_length=8, max_length=128)


class MessageResponse(Schema):
    message: str
