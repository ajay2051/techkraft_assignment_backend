from datetime import datetime
from typing import List

from pydantic import BaseModel, constr, field_validator


class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    # role: str
    phone_number: int
    address: constr(max_length=100)

    @field_validator('first_name')
    def validate_first_name(cls, v):
        first_name_str = str(v)
        if len(first_name_str) < 3 or len(first_name_str) > 15:
            raise ValueError('First name must be between 3 and 10 characters')
        if any(char in r'!@#$%^&*(),.?":{}|<>' for char in v):
            raise ValueError("First Name should not contain any special characters")
        return v

    @field_validator('last_name')
    def validate_last_name(cls, v):
        last_name_str = str(v)
        if len(last_name_str) < 3 or len(last_name_str) > 15:
            raise ValueError('Last name must be between 3 and 10 characters')
        if any(char in r'!@#$%^&*(),.?":{}|<>' for char in v):
            raise ValueError("Last Name should not contain any special characters")
        return v

    @field_validator('phone_number')
    def validate_phone_number(cls, v):
        phone_str = str(v)
        if not (8 <= len(phone_str) <= 15):
            raise ValueError('Phone number must be between 8 and 15 digits')
        if any(char in r'!@#$%^&*(),.?":{}|<>' for char in v):
            raise ValueError("Phone Number should not contain any special characters")
        return v

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    password: constr(max_length=15)

    @field_validator('password')
    def password_must_contain_uppercase_and_symbol(cls, v):
        if len(v) > 15:
            raise ValueError('Password must be 15 characters or less 👎👿⛔')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter 👎👿⛔')
        if not any(char in r'!@#$%^&*(),.?":{}|<>' for char in v):
            raise ValueError('Password must contain at least one symbol 👎👿⛔')
        return v

    class Config:
        from_attributes = True


class UserResponse(UserBase):
    id: int
    role: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateUserResponseMessage(BaseModel):
    message: str = "Account Created Successfully...!👍👍"
    user: UserResponse


class EmailSchema(BaseModel):
    addresses: List[str]


class Token(BaseModel):
    first_name: str
    last_name: str
    access_token: str
    refresh_token: str
    token_type: str
    user_id: int
    email: str
    user_role: str


class LoginData(BaseModel):
    email: str
    password: str


class TokenData(BaseModel):
    email: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
