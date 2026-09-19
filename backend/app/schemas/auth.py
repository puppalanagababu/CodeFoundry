from typing import Optional
from pydantic import BaseModel, EmailStr, Field, model_validator


class UserResponse(BaseModel):
    id: int
    username: str
    email: str = ""
    role: str = "STUDENT"

    model_config = {"from_attributes": True}


class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=150)
    email: Optional[str] = ""
    password: str = Field(..., min_length=6)
    password2: str = Field(..., min_length=6)

    @model_validator(mode="after")
    def validate_passwords_match(self):
        if self.password != self.password2:
            raise ValueError("Passwords do not match.")
        return self


class UserRegisterResponse(BaseModel):
    message: str = "User registered successfully."
    user: UserResponse


class UserLoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access: str
    refresh: str
    user: UserResponse


class TokenRefreshRequest(BaseModel):
    refresh: str = Field(...)


class TokenRefreshResponse(BaseModel):
    access: str
    refresh: str


class LogoutRequest(BaseModel):
    refresh: Optional[str] = None


class MessageResponse(BaseModel):
    message: Optional[str] = None
    detail: Optional[str] = None


class PasswordResetRequest(BaseModel):
    email: str = Field(..., min_length=1)


class PasswordResetConfirmRequest(BaseModel):
    uid: str = Field(..., min_length=1)
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)
    new_password2: str = Field(..., min_length=6)

    @model_validator(mode="after")
    def validate_new_passwords_match(self):
        if self.new_password != self.new_password2:
            raise ValueError("Passwords do not match.")
        return self
