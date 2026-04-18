from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import HTMLResponse, FileResponse
from app.config import CORS_ORIGINS, ENVIRONMENT
from app.routes import auth, complaints, analytics, sse, webhooks, demo, health, users
from app.middleware.exceptions import (
    AppException, app_exception_handler, http_exception_handler,
    validation_exception_handler,
)
import os

app = FastAPI(
    title="TS-14 Complaint Resolution Engine",
    description="AI-Powered Complaint Classification & Resolution System",
    version="1.0.0",
    docs_url="/docs" if ENVIRONMENT == "development" else None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(complaints.router, prefix="/complaints", tags=["Complaints"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(sse.router, prefix="/complaints", tags=["Real-Time SSE"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(demo.router, prefix="/demo", tags=["Demo Mode"])
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(users.router, prefix="/users", tags=["User Management"])


DASHBOARD_DIR = os.environ.get("DASHBOARD_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "..", "voice-agent", "dashboard"))


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_index():
    dashboard_path = os.path.join(DASHBOARD_DIR, "index.html")
    if os.path.exists(dashboard_path):
        return FileResponse(dashboard_path)
    return HTMLResponse("<h1>Dashboard not found</h1><p>Set DASHBOARD_DIR env var to the dashboard directory.</p>")


@app.on_event("startup")
async def startup():
    from app.database import Base, engine
    from app.models import models  # noqa: F401 — ensure tables are registered
    Base.metadata.create_all(bind=engine)
    from app.services.scheduler import start_background_tasks
    start_background_tasks()