import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.app.core.config import settings
from backend.app.core.database import engine, Base
import backend.app.models  # Ensure all 20 models register

# API Routers
from backend.app.api.auth import router as auth_router
from backend.app.api.employees import router as employees_router
from backend.app.api.leave import router as leave_router
from backend.app.api.expenses import router as expenses_router
from backend.app.api.approvals import router as approvals_router
from backend.app.api.policies import router as policies_router
from backend.app.api.decision import router as decision_router
from backend.app.api.reservations import router as reservations_router
from backend.app.api.anomalies import router as anomalies_router
from backend.app.api.audit import router as audit_router
from backend.app.api.analytics import router as analytics_router
from backend.app.api.notifications import router as notifications_router
from backend.app.api.reports import router as reports_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Evidence-First Constraint Graph (EFCG) Intelligent Leave & Expense Management Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for flexible local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Uploads directory
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Include Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(employees_router, prefix=settings.API_V1_STR)
app.include_router(leave_router, prefix=settings.API_V1_STR)
app.include_router(expenses_router, prefix=settings.API_V1_STR)
app.include_router(approvals_router, prefix=settings.API_V1_STR)
app.include_router(policies_router, prefix=settings.API_V1_STR)
app.include_router(decision_router, prefix=settings.API_V1_STR)
app.include_router(reservations_router, prefix=settings.API_V1_STR)
app.include_router(anomalies_router, prefix=settings.API_V1_STR)
app.include_router(audit_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(notifications_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
def startup_event():
    Base.metadata.create_all(bind=engine)

@app.get("/")
def root():
    return {
        "platform": "LeaveFlow EFCG",
        "tagline": "Every Request. Every Decision. Every Reason.",
        "status": "OPERATIONAL",
        "version": "1.0.0",
        "api_docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy", "database": "connected"}
