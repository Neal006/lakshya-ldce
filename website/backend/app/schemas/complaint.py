from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.models import CategoryEnum, PriorityEnum, StatusEnum, SubmittedViaEnum


class CreateComplaintRequest(BaseModel):
    customer_email: str = Field(min_length=5)
    customer_name: str = Field(min_length=1, max_length=255)
    customer_phone: Optional[str] = None
    raw_text: str = Field(min_length=5)
    submitted_via: SubmittedViaEnum = SubmittedViaEnum.dashboard


class UpdateStatusRequest(BaseModel):
    status: StatusEnum
    notes: Optional[str] = None


class EscalateRequest(BaseModel):
    reason: str = Field(min_length=1)


class CustomerBriefResponse(BaseModel):
    id: Optional[str] = None
    name: str
    email: str
    phone: Optional[str] = None

    model_config = {"from_attributes": True}


class CustomerNameOnlyResponse(BaseModel):
    name: str


class TimelineEntryResponse(BaseModel):
    id: str
    action: str
    performed_by: Optional[dict] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ComplaintResponse(BaseModel):
    id: str
    customer_id: str
    customer: CustomerBriefResponse
    raw_text: str
    category: Optional[str] = None
    priority: Optional[str] = None
    resolution_steps: Optional[list[str]] = None
    sentiment_score: Optional[float] = None
    status: str
    submitted_via: str
    sla_deadline: Optional[datetime] = None
    sla_breached: bool = False
    created_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class ComplaintDetailResponse(ComplaintResponse):
    timeline: list[TimelineEntryResponse] = []


class ComplaintListItemResponse(BaseModel):
    id: str
    customer: CustomerBriefResponse
    raw_text: str
    category: Optional[str] = None
    priority: Optional[str] = None
    status: str
    sla_deadline: Optional[datetime] = None
    sla_breached: bool = False
    created_at: Optional[datetime] = None


class CallAttenderListItemResponse(BaseModel):
    id: str
    customer: CustomerNameOnlyResponse
    raw_text: str
    resolution_steps: Optional[list[str]] = None
    status: str
    created_at: Optional[datetime] = None


class PaginationResponse(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class ComplaintListResponse(BaseModel):
    complaints: list[ComplaintListItemResponse]
    pagination: PaginationResponse


class CallAttenderListResponse(BaseModel):
    complaints: list[CallAttenderListItemResponse]
    pagination: PaginationResponse


class StatusUpdateResponse(BaseModel):
    id: str
    status: str
    updated_at: Optional[datetime] = None
    timeline: list[TimelineEntryResponse] = []

    model_config = {"from_attributes": True}


class EscalateResponse(BaseModel):
    id: str
    status: str
    escalation_reason: str
    escalated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class DataWrapperComplaint(BaseModel):
    data: dict


class DataWrapperComplaintDetail(BaseModel):
    data: dict


class DataWrapperComplaintList(BaseModel):
    data: dict


class DataWrapperCallAttenderList(BaseModel):
    data: dict


class DataWrapperStatusUpdate(BaseModel):
    data: dict


class DataWrapperEscalate(BaseModel):
    data: dict