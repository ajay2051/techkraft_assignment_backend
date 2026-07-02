import datetime

from sqlalchemy import ARRAY, TIMESTAMP, BigInteger, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.db_connection import Base
from app.enums import UserRole, CandidateStatus


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    phone_number = Column(BigInteger, unique=True)
    address = Column(String)
    role = Column(String, default=UserRole.REVIEWER.value)

    scores = relationship("Scores", back_populates="reviewer", cascade="all, delete-orphan")

    created_at = Column(TIMESTAMP, default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now(), nullable=False)


    def __repr__(self):
        return f"{self.email}"


class BlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True)
    blacklisted_on = Column(DateTime, default=datetime.datetime.utcnow)


class Candidates(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    role_applied = Column(String, index=True)
    status = Column(String, default=CandidateStatus.NEW.value, index=True)
    skills = Column(ARRAY(String), default=list)
    internal_notes = Column(String, nullable=True)
    keywords = Column(String, nullable=True)

    scores = relationship("Scores", back_populates="candidate", cascade="all, delete-orphan")

    created_at = Column(TIMESTAMP, default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now(), nullable=False)



class Scores(Base):
    __tablename__ = "scores"
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, index=True)
    score = Column(Integer, index=True)
    notes = Column(String, nullable=True)

    candidate_id = Column(Integer, ForeignKey('candidates.id'), nullable=False, index=True)
    candidate = relationship("Candidates", back_populates="scores")

    reviewer_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    reviewer = relationship("User", back_populates="scores")

    created_at = Column(TIMESTAMP, default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now(), nullable=False)
