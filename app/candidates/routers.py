import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import cast, String
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from fastapi.params import Query
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.auth.dependencies import AllowedUsers
from app.auth.jwt_token import get_current_user
from app.candidates import schemas
from app.candidates.get_create_candidates import get_candidates_by_email, create_candidate, get_candidates_by_id, get_candidates_with_scores
from app.candidates.schemas import CreateCandidateResponseMessage, CandidateResponse, CandidateStatuss
from app.custom_exceptions import CandidateAlreadyExists, CandidateDoesNotExists
from app.db_connection import get_db
from app.enums import CandidateStatus
from app.models import Candidates, Scores
from app.pagination import paginate

candidate_router = APIRouter(tags=["Candidate"])


@candidate_router.post("/create_candidate/", response_model=schemas.CreateCandidateResponseMessage)
async def create_candidates(candidate: schemas.CandidateCreate, db: Session = Depends(get_db)):
    can = get_candidates_by_email(db, candidate.email)
    if can:
        raise CandidateAlreadyExists
    new_candidate = create_candidate(db, candidate)
    return CreateCandidateResponseMessage(candidate=new_candidate)


@candidate_router.get("/list_candidates/")
async def get_candidates(
        request: Request,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(20, ge=1, le=50, description="Items per page"),
        status: str = Query(None, description="Filter by brand"),
        role_applied: str = Query(None, description="Filter by location"),
        skills: str = Query(None, description="Filter by vehicle type"),
        keywords: str = Query(None, description="Filter by fuel type"),
        db: Session = Depends(get_db),
        current_user: int = Depends(get_current_user)
):
    query = db.query(Candidates).filter(Candidates.status != CandidateStatus.ARCHIVED.value)

    if current_user.role == "reviewer":
        query = (query.join(Scores).filter(Scores.reviewer_id == current_user.id,).distinct())

    if status:
        query = query.filter(Candidates.status == status)
    if skills:
        skills_types = [sk.strip() for sk in skills.split(',')]
        query = query.filter(cast(Candidates.skills, PG_ARRAY(String)).overlap(skills_types))
    if role_applied:
        query = query.filter(Candidates.role_applied == role_applied)
    if keywords:
        query = query.filter(Candidates.keywords.ilike(f"%{keywords}%"))
    total_objects = query.count()
    paginated_query = query.offset((page - 1) * per_page).limit(per_page)
    data = await paginate(model=Candidates, db=db, query=paginated_query, page=page, per_page=per_page, request=request, response_model_schema=CandidateResponse, objects=total_objects)
    if current_user.role == "reviewer":
        for item in data.items:
            item["scores"] = [s for s in item["scores"] if s["reviewer_id"] == current_user.id]
    return {"message": "Candidates listed successfully...👍🔥", "data": data}


@candidate_router.get("/{id}/")
async def get_candidate(id: int, db: Session = Depends(get_db), current_user: int = Depends(get_current_user)):
    candidate = get_candidates_with_scores(db=db, candidate_id=id)
    if not candidate:
        raise CandidateDoesNotExists
    return {"message": "Candidate details successfully...", "data": candidate}


@candidate_router.get("/{id}/summary")
async def summarize_candidate(id: int, db: Session = Depends(get_db), current_user: int = Depends(get_current_user),):

    candidate = get_candidates_with_scores(db=db, candidate_id=id)

    if not candidate:
        raise CandidateDoesNotExists

    # Prepare prompt for the LLM
    prompt = f"""
    Summarize the following candidate for a recruiter.

    Name: {candidate['name']}
    Role Applied: {candidate['role_applied']}
    Skills: {', '.join(candidate['skills'])}
    Status: {candidate['status']}
    Internal Notes: {candidate['internal_notes']}
    Reviews: {candidate['scores']}

    Return a concise professional summary and recommendation.
    """


    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "http://localhost:8001/mock-llm",
            json={
                "model": "gpt-4.1-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert HR recruiter."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }
        )

    response.raise_for_status()
    llm_response = response.json()
    return {"message": "Candidate summary generated successfully.", "candidate": candidate, "summary": llm_response["summary"],}


@candidate_router.patch("/{id}/")
async def update_candidate_internal_notes(id: int, candidates: schemas.CandidateInternalNotes, db: Session = Depends(get_db), current_user: int = Depends(get_current_user),
                                          _: bool = Depends(AllowedUsers(["admin"]))):
    candidate = get_candidates_by_id(db=db, candidate_id=id)
    if not candidate:
        raise CandidateDoesNotExists
    for field, value in candidates.dict().items():
        setattr(candidate, field, value)
    db.commit()
    db.refresh(candidate)
    return {"message": "Candidate details updated successfully...", "data": candidate}


@candidate_router.patch("/{id}/status/")
async def update_candidate_status(id: int, candidates: CandidateStatuss, db: Session = Depends(get_db), current_user: int = Depends(get_current_user),
                                  _: bool = Depends(AllowedUsers(["admin"]))):
    candidate = get_candidates_by_id(db=db, candidate_id=id)
    if not candidate:
        raise CandidateDoesNotExists
    for field, value in candidates.dict().items():
        setattr(candidate, field, value)
    db.commit()
    db.refresh(candidate)
    return {"message": "Candidate status updated successfully...", "data": candidate}


@candidate_router.delete("/{id}/")
async def soft_delete_candidate(id: int, db: Session = Depends(get_db), current_user: int = Depends(get_current_user),
                                _: bool = Depends(AllowedUsers(["admin"]))
                                ):
    candidate = get_candidates_by_id(db=db, candidate_id=id)

    if not candidate:
        raise CandidateDoesNotExists

    # Already archived
    if candidate.status == CandidateStatus.ARCHIVED.value:
        return {"message": "Candidate is already archived.", "data": candidate}

    candidate.status = CandidateStatus.ARCHIVED.value

    db.commit()
    db.refresh(candidate)

    return {"message": "Candidate archived successfully.", "data": candidate}
