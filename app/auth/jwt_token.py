import os
from datetime import datetime, timedelta

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from itsdangerous import URLSafeTimedSerializer
from jose import JWTError
from jwt import ExpiredSignatureError
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from starlette import status

from app import models
from app.auth import schemas
from app.auth.get_create_user import get_user_by_email
from app.custom_exceptions import InvalidCredentials, InvalidRefreshToken, TokenBlacklisted, UserNotFound
from app.db_connection import get_db
from app.models import User

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = float(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS = float(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS"))
serializer = URLSafeTimedSerializer(secret_key=SECRET_KEY, salt="email-configuration")


def verify_password(plain_password, hashed_password):
    """
    Verify Password with user entered password
    :param plain_password:
    :param hashed_password:
    :return:
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    """
    Hashes plain password
    :param password:
    :return: hashed_password
    """
    return pwd_context.hash(password)


def authenticate_user(db: Session, email: str, password: str):
    """
    Authenticate user by comparing user entered email and password with database email and password
    :param db:
    :param email:
    :param password:
    :return: user
    """
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
        Create Access Token for Authenticated User
        :param data:
        :param expires_delta:
        :return:
        """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict):
    """
    Create Refresh Token for Authenticated User
    :param data:
    :return:
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_refresh_token(token: str):
    """
    Verify Refresh Token for Authenticated User
    :param token:
    :return: token_data
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        if email is None or token_type != "refresh":
            raise InvalidRefreshToken
        token_data = schemas.TokenData(email=email)
        return token_data
    except jwt.ExpiredSignatureError:
        raise InvalidRefreshToken


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Get Current User
    :param token:
    :param db:
    :return:
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise InvalidCredentials
        token_data = schemas.TokenData(email=email)
    except ExpiredSignatureError:
        # Token was valid but expired
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    except JWTError:
        # Token is malformed / invalid
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if is_token_blacklisted(db, token):
        raise TokenBlacklisted
    user = get_user_by_email(db, email=token_data.email)
    if user is None:
        raise UserNotFound
    return user


def blacklist_token(db: Session, token: str):
    """
    Blacklisted Token after logout
    :param db:
    :param token:
    :return:
    """
    db_token = models.BlacklistedToken(token=token)
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    return db_token


def is_token_blacklisted(db: Session, token: str) -> bool:
    """
    Checks if token is blacklisted
    :param db:
    :param token:
    :return:
    """
    return db.query(models.BlacklistedToken).filter(models.BlacklistedToken.token == token).first() is not None
