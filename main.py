import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.auth.routers import auth_router
from app.candidates.routers import candidate_router
from app.custom_exceptions import register_all_errors
from app.db_connection import startup, shutdown
from app.scores.routers import score_router
from config import MODE

version = "v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Server Starting.....")
    await startup()
    yield
    await shutdown()
    print("Server Stopped.....")


app = FastAPI(
    title="API",
    description=f"{version} - REST API",
    version=version,
    lifespan=lifespan,
    docs_url=f"/api/{version}/docs",
    redoc_url=f"/api/{version}/redoc",
    contact={
        "phone": "+977 9864915625",
        "email": "ajaythk.94@gmail.com",

    }
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Trusted Host middleware
# app.add_middleware(
#     TrustedHostMiddleware,
#     allowed_hosts=['127.0.0.1', 'localhost',]
# )


@app.get("/")
def welcome_to_candidate_evaluation():
    return {"message": "Welcome to Candidate Evaluation API... 🙏🙏"}


register_all_errors(app)  # Register All Errors from custom_exception file in main file

app.include_router(auth_router, prefix=f"/api/{version}/auth")
app.include_router(candidate_router, prefix=f"/api/{version}/candidate")
app.include_router(score_router, prefix=f"/api/{version}")

# Run Project At Specified Port
if __name__ == "__main__":
    if MODE == "development":
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    else:
        # For production, let the platform set the port
        port = int(os.getenv("PORT", 8000))
        uvicorn.run("main:app", host="127.0.0.1", port=port, reload=False)
