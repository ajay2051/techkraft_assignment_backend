from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import schemas, jwt_token
from app.auth.get_create_user import get_user_by_email, get_user_by_number, create_user
from app.auth.jwt_token import blacklist_token
from app.auth.schemas import CreateUserResponseMessage, LoginData
from app.custom_exceptions import UserAlreadyExists, UserNotFound, IncorrectEmailPassword
from app.db_connection import get_db
from app.enums import UserRole

auth_router = APIRouter(tags=["Auth"])


@auth_router.post("/create_reviewer_user/", response_model=schemas.CreateUserResponseMessage)
async def create_users(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if db_user:
        raise UserAlreadyExists
    user_by_number = get_user_by_number(db, user.phone_number)
    if user_by_number:
        raise UserAlreadyExists
    role = UserRole.REVIEWER.value
    new_user = create_user(db, role, user)
    return CreateUserResponseMessage(user=new_user)


@auth_router.post("/create_admin_user/", response_model=schemas.CreateUserResponseMessage)
async def create_users(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = get_user_by_email(db, user.email)
    if db_user:
        raise UserAlreadyExists
    user_by_number = get_user_by_number(db, user.phone_number)
    if user_by_number:
        raise UserAlreadyExists
    role = UserRole.ADMIN.value
    new_user = create_user(db, role, user)
    return CreateUserResponseMessage(user=new_user)


@auth_router.post("/token/refresh/", response_model=schemas.TokenResponse)
async def refresh_access_token(token: str, db: Session = Depends(get_db)):
    """
    Generate a new access token using a valid refresh token.

    This endpoint allows users to obtain a new access token without
    having to log in again by providing a valid refresh token.
    """
    token_data = jwt_token.verify_refresh_token(token)
    user = get_user_by_email(db, token_data.get('email'))
    if not user:
        raise UserNotFound
    access_token_expires = timedelta(minutes=jwt_token.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt_token.create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    refresh_token = jwt_token.create_refresh_token(data={"sub": user.email})
    return {"token_type": "Bearer", "access_token": access_token, "refresh_token": refresh_token}


@auth_router.post("/login/", response_model=schemas.Token)
async def login_for_access_token(form_data: LoginData, db: Session = Depends(get_db)):
    """
    Authenticate a user and generate access and refresh tokens.

    This endpoint verifies the user's credentials and, if valid, provides
    access and refresh tokens for authenticated API access. The user must
    have a verified account to log in.

    Args:
        form_data: User credentials containing email and password
        db: Database session dependency

    Returns:
        Token: Object containing access token, refresh token, token type, user ID, email, and role

    Raises:
        UserNotFound: If the user with the provided email doesn't exist
        UserNotVerified: If the user account has not been verified
        IncorrectEmailPassword: If the provided password is incorrect
    """
    email_user = get_user_by_email(db, form_data.email)
    if not email_user:
        raise UserNotFound
    user = jwt_token.authenticate_user(db, form_data.email, form_data.password)
    if not user:
        raise IncorrectEmailPassword
    access_token_expires = timedelta(minutes=jwt_token.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = jwt_token.create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    refresh_token = jwt_token.create_refresh_token(data={"sub": user.email})
    return {"token_type": "Bearer", "access_token": access_token, "refresh_token": refresh_token, "user_id": user.id, "email": user.email,
            "user_role": user.role, "first_name": user.first_name, "last_name": user.last_name}


@auth_router.post("/logout/")
async def logout(current_user: schemas.UserResponse = Depends(jwt_token.get_current_user), token: str = Depends(jwt_token.oauth2_scheme),
                 db: Session = Depends(get_db)):
    blacklist_token(db, token)
    return {"message": "Successfully logged out 👍🙂"}
