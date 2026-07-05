"""
tests/test_candidates.py

Covers:
1. test_create_candidate            - basic API endpoint test (create + verify response)
2. test_create_duplicate_candidate  - same endpoint, duplicate-email rejection path
3. test_reviewer_sees_only_own_scores       - auth/role enforcement (reviewer A)
4. test_reviewer_cannot_see_other_reviewer_scores - auth/role enforcement (reviewer B
   gets a disjoint set from reviewer A, proving isolation between reviewers)

These rely on the `client`, `db_session`, and `as_user` fixtures defined in
conftest.py, which give each test a clean, isolated database and let us
simulate whichever logged-in user we need without a real login/token flow.

NOTE on reviewer ids: Scores.reviewer_id has a real foreign key to users.id,
so tests must create actual User rows and use their generated ids - not
made-up numbers - or Postgres will reject the insert with a
ForeignKeyViolation. `_make_reviewer` below handles that.

Adjust the import path below (`app.models`) if your User / Candidates /
Scores classes actually live somewhere else.
"""
from app.models import User, Candidates, Scores
from app.enums import CandidateStatus, UserRole
from conftest import FakeUser


# ---------------------------------------------------------------------------
# 1 & 2: API endpoint tests for candidate creation
# ---------------------------------------------------------------------------

def test_create_candidate(client):
    payload = {
        "name": "JohnDoe",
        "email": "john@example.com",
        "role_applied": "Python Developer",
        "skills": ["python", "fastapi"],
        "keywords": "backend",
    }

    response = client.post("/api/v1/candidate/create_candidate/", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Candidate Created Successfully...!👍👍"
    assert body["candidate"]["email"] == payload["email"]
    assert body["candidate"]["name"] == payload["name"]
    assert body["candidate"]["role_applied"] == payload["role_applied"]
    assert body["candidate"]["skills"] == payload["skills"]


def test_create_duplicate_candidate(client):
    payload = {
        "name": "JaneDoe",
        "email": "duplicate@example.com",
        "role_applied": "Python Developer",
        "skills": ["python"],
        "keywords": "backend",
    }

    first = client.post("/api/v1/candidate/create_candidate/", json=payload)
    assert first.status_code == 200

    second = client.post("/api/v1/candidate/create_candidate/", json=payload)
    assert second.status_code == 400


# ---------------------------------------------------------------------------
# 3 & 4: Auth enforcement - a reviewer can only see scores tied to them
# ---------------------------------------------------------------------------

def _make_reviewer(db_session, email):
    """Create a real User row (role=reviewer) and return it with its DB-assigned id."""
    reviewer = User(
        first_name="Test",
        last_name="Reviewer",
        email=email,
        password="not-a-real-hash",
        role=UserRole.REVIEWER.value,
    )
    db_session.add(reviewer)
    db_session.commit()
    db_session.refresh(reviewer)
    return reviewer


def _seed_candidate_with_scores(db_session, name, email, reviewer_ids):
    """
    Helper: create one candidate and one Score row per reviewer id given.
    reviewer_ids must be ids of Users that already exist (see _make_reviewer),
    since Scores.reviewer_id is a real foreign key to users.id.
    """
    candidate = Candidates(
        name=name,
        email=email,
        role_applied="Python Developer",
        skills=["python"],
        keywords="backend",
        status=CandidateStatus.NEW.value,
    )
    db_session.add(candidate)
    db_session.flush()  # get candidate.id without committing

    for reviewer_id in reviewer_ids:
        db_session.add(Scores(
            candidate_id=candidate.id,
            reviewer_id=reviewer_id,
            score=4,
            category="technical",
            notes="Solid technical interview.",
        ))

    db_session.commit()
    return candidate


def test_reviewer_sees_only_own_scores(client, db_session, as_user):
    reviewer_a = _make_reviewer(db_session, "reviewer.a@example.com")
    reviewer_b = _make_reviewer(db_session, "reviewer.b@example.com")

    # Candidate reviewed by both reviewers
    _seed_candidate_with_scores(
        db_session, "CandOne", "cand.one@example.com",
        reviewer_ids=[reviewer_a.id, reviewer_b.id],
    )

    as_user(FakeUser(id=reviewer_a.id, role="reviewer"))

    response = client.get("/api/v1/candidate/list_candidates/")
    assert response.status_code == 200

    items = response.json()["data"]["items"]
    assert len(items) >= 1
    for candidate in items:
        for score in candidate["scores"]:
            assert score["reviewer_id"] == reviewer_a.id


def test_reviewer_cannot_see_other_reviewer_scores(client, db_session, as_user):
    reviewer_a = _make_reviewer(db_session, "reviewer.a@example.com")
    reviewer_b = _make_reviewer(db_session, "reviewer.b@example.com")

    # Two separate candidates, each scored by a different, single reviewer
    _seed_candidate_with_scores(
        db_session, "CandA", "cand.a@example.com", reviewer_ids=[reviewer_a.id]
    )
    _seed_candidate_with_scores(
        db_session, "CandB", "cand.b@example.com", reviewer_ids=[reviewer_b.id]
    )

    as_user(FakeUser(id=reviewer_b.id, role="reviewer"))

    response = client.get("/api/v1/candidate/list_candidates/")
    assert response.status_code == 200

    items = response.json()["data"]["items"]
    seen_emails = {c["email"] for c in items}

    # Reviewer B should see CandB but never CandA (which only reviewer A scored)
    assert "cand.b@example.com" in seen_emails
    assert "cand.a@example.com" not in seen_emails

    for candidate in items:
        for score in candidate["scores"]:
            assert score["reviewer_id"] == reviewer_b.id