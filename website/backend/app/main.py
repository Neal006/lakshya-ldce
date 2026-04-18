from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import CORS_ORIGINS, ENVIRONMENT
from app.routes import auth, complaints, analytics, sse, webhooks, demo, health

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

app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(complaints.router, prefix="/complaints", tags=["Complaints"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(sse.router, prefix="/complaints", tags=["Real-Time SSE"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])
app.include_router(demo.router, prefix="/demo", tags=["Demo Mode"])
app.include_router(health.router, prefix="/health", tags=["Health"])


@app.on_event("startup")
async def startup():
    from app.database import Base, engine
    Base.metadata.create_all(bind=engine)