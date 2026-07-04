# Backend - TechKraft Candidate Assessment API

This repository contains the **backend service** for the TechKraft Candidate Assessment System built with **FastAPI**, **PostgreSQL**, and **JWT Authentication**.

---

# Features

* FastAPI REST API
* JWT Authentication
* Role-Based Access Control (Reviewer/Admin)
* Candidate Management
* Candidate Search with Filtering
* Offset-based Pagination
* Candidate Scoring
* Soft Delete Support
* Docker Support

---

# Tech Stack

* Python 3.11+
* FastAPI
* SQLAlchemy
* PostgreSQL
* Pydantic
* Passlib (bcrypt)
* Python-Jose (JWT)
* Pytest

---

# Installation

## Clone Repository

```bash
git clone https://github.com/ajay2051/techkraft_assignment_backend

cd backend
```

## Create Virtual Environment

```bash
python -m venv venv
```

Linux/Mac

```bash
source venv/bin/activate
```

Windows

```bash
venv\Scripts\activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Environment Variables

Create a `.env` file using `.env.example`.

Example:

```env
MODE=development
DATABASE_HOSTNAME=DATABASE_HOSTNAME
DATABASE_PORT=DATABASE_PORT
DATABASE_PASSWORD=DATABASE_PASSWORD
DATABASE_NAME=DATABASE_NAME
DATABASE_USERNAME=DATABASE_USERNAME
SECRET_KEY=SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS=REFRESH_TOKEN_EXPIRE_DAYS

DOMAIN=http:127.0.0.1:8000

UI_DOMAIN="rental-henna-mu.vercel.app"

REDIS_HOST=redis
REDIS_HOST_LOCAL=localhost
REDIS_PORT=6397
REDIS_URL=redis://redis:6379/0
```

**Important**

* Never commit real credentials.
* Only `.env.example` should be committed.

---

# Run the Server

```bash
fastapi dev
```

API URL

```
http://127.0.0.1:8000/api/v1/
```

Swagger Documentation

```
http://127.0.0.1:8000/api/v1/docs
```

ReDoc

```
http://localhost:8000/redoc
```

---

# Authentication

The application uses JWT authentication.

# Role-Based Access Control

## Reviewer

* Login
* View candidate list
* View candidate details
* View only their own scores
* Submit scores
* Cannot view internal notes

---

## Admin

* Full access
* View every reviewer's score
* View internal notes
* Edit internal notes

---

# Database Schema

## Candidates

| Column         | Description                          |
| -------------- | ------------------------------------ |
| id             | Primary Key                          |
| name           | Candidate Name                       |
| email          | Email                                |
| role_applied   | Applied Position                     |
| status         | new/reviewed/hired/rejected/archived |
| skills         | List of Skills                       |
| internal_notes | Admin Only                           |
| created_at     | Timestamp                            | |

Indexes

* status
* role_applied

---

## Scores

| Column       | Description         |
| ------------ | ------------------- |
| id           | Primary Key         |
| candidate_id | Foreign Key         |
| category     | Evaluation Category |
| score        | 1–5                 |
| reviewer_id  | Reviewer            |
| note         | Optional            |
| created_at   | Timestamp           |

Index

* candidate_id

---

Included tests

* Candidate API endpoint
* Authentication enforcement
* Reviewer cannot view another reviewer's scores


---

# Architecture Decision Record (ADR)

## Decision 1 – FastAPI

### Context

The project requires asynchronous endpoints, validation, JWT authentication, and automatic API documentation.

### Decision

Use FastAPI.

### Trade-off

FastAPI requires Python type hints and Pydantic models but provides excellent performance, async support, and interactive API documentation.

---

## Decision 2 – PostgreSQL

### Context

Best database for production.

### Decision

Use PostgreSQL with SQLAlchemy ORM.

---

## Decision 3 – Server-side RBAC

### Context

Clients should never be trusted to assign privileged roles.

### Decision

Registration always creates users with the Reviewer role, while authorization is enforced using JWT claims on the server.

### Trade-off

Admin accounts must be created separately, but the system is protected against role spoofing.

---

# Learning Reflection

While building this project, I explored implementing role-based access control using JWT claims and server-side authorization. 
Given more time, I would integrate a background task queue such as Celery or Redis for AI summary generation and fully implement the Server-Sent Events endpoint for real-time score updates.

---

# Notes

* Registration always creates a **Reviewer**.
* No credentials are committed to the repository.
* Offset-based pagination uses a default limit of **20** and a maximum limit of **50**.



alembic -n tech revision --autogenerate -m "initial"

alembic -n tech upgrade head

    
            Users

            +------------+
            | id         |
            | name       |
            +------------+
                  |
                  | 1
                  |
                  | *
            +------------+
            | Scores     |
            +------------+
            | id         |
            | category   |
            | score      |
            | reviewer_id|
            |candidate_id|
            +------------+
                  |
                  | *
                  |
                  | 1
           +---------------+
           | Candidates    |
           +---------------+
           | id            |
           | name          |
           +---------------+


# Debugging Signal

The core issue is that the code retrieves every row from the database and performs filtering and pagination in application code instead of letting the database do that work.

What's wrong?
all_candidates = db.execute("SELECT * FROM candidates").fetchall()

This statement loads the entire candidates table into memory regardless of:

the requested status
the search keyword
the requested page
the requested page size

Then the application performs:

filtered = [c for c in all_candidates if c["status"] == status]

and later slices the list for pagination.

Why this matters at scale

This pattern works on a small development database but becomes increasingly expensive as the dataset grows.

Problems include:

Unnecessary I/O
Every request transfers the entire table from the database.
Network traffic grows linearly with table size.
High memory usage
The application stores every candidate in memory.
Large tables can significantly increase memory consumption or even exhaust available memory.
Poor CPU utilization
Filtering in Python is much slower than using indexed database queries.
Every request scans every record.
Inefficient pagination
To return 20 records on page 50, the application still reads all rows first.
Pagination provides no performance benefit because the full dataset has already been loaded.
Poor scalability
As the table grows from thousands to millions of rows, response times increase dramatically.
Concurrent requests multiply the wasted work.
The correct approach

Filtering and pagination should be performed in SQL so the database optimizer can use indexes and return only the requested rows.

Example:

def search_candidates(status: str, keyword: str, page: int, page_size: int):
    offset = (page - 1) * page_size

    return db.execute(
        """
        SELECT *
        FROM candidates
        WHERE status = ?
          AND (
                name LIKE ?
                OR resume_text LIKE ?
              )
        ORDER BY id
        LIMIT ? OFFSET ?
        """,
        (
            status,
            f"%{keyword}%",
            f"%{keyword}%",
            page_size,
            offset,
        ),
    ).fetchall()