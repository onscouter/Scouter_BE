import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import auth, recruiter, role
from app.db.session import engine
from app.models import base
from app.rate_limiter import limiter

# Constants
API_PREFIX = "/api"
APP_NAME = "Scouter Interview Assistant"
APP_VERSION = "1.0.0"

# Create app
app = FastAPI(title=APP_NAME, version=APP_VERSION)

# Attach limiter instance
app.state.limiter = limiter


def setup_middlewares(app: FastAPI) -> None:
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        SessionMiddleware,
        secret_key=os.getenv("SESSION_SECRET_KEY", "dev-secret"),  # default for dev
    )


def setup_routers(app: FastAPI) -> None:
    app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
    app.include_router(recruiter.router, prefix="/api/recruiter", tags=["Recruiter"])
    app.include_router(role.router, prefix="/api/role", tags=["Role"])

    # app.include_router(view_applicaiton.router, prefix="/api/application", tags=["View Application"])
    # app.include_router(interviews.router, prefix="/interviews", tags=["Interviews"])


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Try again later."},
    )


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.on_event("startup")
def on_startup():
    base.Base.metadata.create_all(bind=engine)
    print(f"{APP_NAME} v{APP_VERSION} startup complete")


@app.on_event("shutdown")
def on_shutdown():
    print(f"{APP_NAME} shutdown complete")


@app.get("/")
def root():
    return {"message": "API is running!"}


setup_middlewares(app)
setup_routers(app)
