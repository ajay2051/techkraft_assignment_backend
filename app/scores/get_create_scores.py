from datetime import datetime

from sqlalchemy.orm import Session

from app import models
from app.scores import schemas


def get_score_by_id(db: Session, score_id):
    return db.query(models.Scores).filter(models.Scores.id == score_id).first()


def create_score(db: Session, candidate_id: int, reviewer_id: int,  score: schemas.ScoreCreate):
    new_score = models.Scores(
        category=score.category,
        score=score.score,
        notes=score.notes,
        candidate_id=candidate_id,
        reviewer_id=reviewer_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow())
    db.add(new_score)
    db.commit()
    db.refresh(new_score)
    return new_score
