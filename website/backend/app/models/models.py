import uuid
import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Float, Integer, ForeignKey, Enum, DateTime, Boolean
)
from sqlalchemy.orm import relationship
from app.database import Base
from app.services.utils import generate_uuid7


class RoleEnum(str, enum.Enum):
    admin = "admin"
    qa = "qa"
    call_attender = "call_attender"


class CategoryEnum(str, enum.Enum):
    product = "Product"
    packaging = "Packaging"
    trade = "Trade"


class PriorityEnum(str, enum.Enum):
    high = "High"
    medium = "Medium"
    low = "Low"


class StatusEnum(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    escalated = "escalated"


class SubmittedViaEnum(str, enum.Enum):
    email = "email"
    call = "call"
    dashboard = "dashboard"


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid7())
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.call_attender)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    complaints = relationship("Complaint", back_populates="created_by_profile", foreign_keys="Complaint.created_by")
    timeline_entries = relationship("ComplaintTimeline", back_populates="performed_by_profile")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid7())
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    complaints = relationship("Complaint", back_populates="customer")


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid7())
    customer_id = Column(String(36), ForeignKey("customers.id"), nullable=False, index=True)
    raw_text = Column(Text, nullable=False)
    category = Column(Enum(CategoryEnum), nullable=True)
    priority = Column(Enum(PriorityEnum), nullable=True)
    resolution_steps = Column(Text, nullable=True)
    sentiment_score = Column(Float, nullable=True)
    status = Column(Enum(StatusEnum), default=StatusEnum.open, nullable=False, index=True)
    submitted_via = Column(Enum(SubmittedViaEnum), nullable=False, default=SubmittedViaEnum.dashboard)
    escalation_reason = Column(Text, nullable=True)
    sla_deadline = Column(DateTime, nullable=True)
    sla_breached = Column(Boolean, default=False)
    created_by = Column(String(36), ForeignKey("profiles.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    escalated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    customer = relationship("Customer", back_populates="complaints")
    created_by_profile = relationship("Profile", back_populates="complaints", foreign_keys=[created_by])
    timeline = relationship("ComplaintTimeline", back_populates="complaint", order_by="ComplaintTimeline.created_at")


class ComplaintTimeline(Base):
    __tablename__ = "complaint_timeline"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid7())
    complaint_id = Column(String(36), ForeignKey("complaints.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    performed_by = Column(String(36), ForeignKey("profiles.id"), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    complaint = relationship("Complaint", back_populates="timeline")
    performed_by_profile = relationship("Profile", back_populates="timeline_entries")


class SLAConfig(Base):
    __tablename__ = "sla_config"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid7())
    priority = Column(Enum(PriorityEnum), unique=True, nullable=False)
    deadline_hours = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class DailyMetrics(Base):
    __tablename__ = "daily_metrics"

    id = Column(String(36), primary_key=True, default=lambda: generate_uuid7())
    date = Column(DateTime, nullable=False, index=True)
    total_complaints = Column(Integer, default=0)
    open_complaints = Column(Integer, default=0)
    resolved_complaints = Column(Integer, default=0)
    escalated_complaints = Column(Integer, default=0)
    avg_resolution_time_hours = Column(Float, nullable=True)
    sla_compliance_rate = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))