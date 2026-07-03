from datetime import datetime

from sqlalchemy.orm import Session

from app import models
from app.auth import jwt_token, schemas


def get_user_by_id(db: Session, user_id):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == str(email)).first()


def get_user_by_number(db: Session, phone_number: int):
    return db.query(models.User).filter(models.User.phone_number == phone_number).first()


def create_user(db: Session, role: str, user: schemas.UserCreate):
    hashed_password = jwt_token.get_password_hash(user.password)
    # db_user = User(**user.model_dump())
    db_user = models.User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        password=hashed_password,
        phone_number=user.phone_number,
        address=user.address,
        role=role,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


async def update_user(db: Session, user: models.User, user_data: dict):
    for key, value in user_data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user
