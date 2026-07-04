from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import AllowedUsers
from app.auth.jwt_token import get_current_user
from app.candidates.get_create_candidates import get_candidates_by_id
from app.custom_exceptions import CandidateDoesNotExists, ScoreDoesNotExists
from app.db_connection import get_db
from app.scores import schemas
from app.scores.get_create_scores import create_score, get_score_by_id
from app.scores.schemas import CreateScoreResponseMessage

score_router = APIRouter(tags=["Score"])


@score_router.post("/candidates/{id}/scores/", response_model=schemas.CreateScoreResponseMessage)
async def create_scores(id: int, score: schemas.ScoreCreate, db: Session = Depends(get_db),
                        current_user: int = Depends(get_current_user),
                        _: bool = Depends(AllowedUsers(["reviewer"]))
                        ):
    can = get_candidates_by_id(db, id)
    if not can:
        raise CandidateDoesNotExists
    new_score = create_score(db, candidate_id=id, reviewer_id=current_user.id, score=score)
    return CreateScoreResponseMessage(score=new_score)


@score_router.patch("/candidates/{candidate_id}/scores/{score_id}/")
async def update_scores(candidate_id: int, score_id: int, scores: schemas.ScoreCreate, db: Session = Depends(get_db),
                        current_user: int = Depends(get_current_user),
                        _: bool = Depends(AllowedUsers(["admin"]))):
    candidate = get_candidates_by_id(db=db, candidate_id=candidate_id)
    if not candidate:
        raise CandidateDoesNotExists
    score = get_score_by_id(db, score_id)
    if not score:
        raise ScoreDoesNotExists
    for field, value in scores.dict().items():
        setattr(score, field, value)
    db.commit()
    db.refresh(score)
    return {"message": "Score details updated successfully...", "data": score}
