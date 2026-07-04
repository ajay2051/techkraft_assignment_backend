from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app import models
from app.candidates import schemas
from app.models import Candidates


def get_candidates_by_id(db: Session, candidate_id: int):
    return db.query(Candidates).filter(Candidates.id == candidate_id).first()


def get_candidates_with_scores(db: Session, candidate_id: int):
    return db.query(Candidates).options(joinedload(Candidates.scores)).filter(Candidates.id == candidate_id).first()


def get_candidates_by_email(db: Session, email: str):
    return db.query(models.Candidates).filter(models.Candidates.email == str(email)).first()


def create_candidate(db: Session, candidate: schemas.CandidateCreate):
    new_candidate = models.Candidates(
        name=candidate.name,
        email=candidate.email,
        role_applied=candidate.role_applied,
        skills=candidate.skills,
        keywords=candidate.keywords,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow())
    db.add(new_candidate)
    db.commit()
    db.refresh(new_candidate)
    return new_candidate
