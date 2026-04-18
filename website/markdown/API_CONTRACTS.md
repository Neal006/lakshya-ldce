# API Contracts — TS-14 Complaint Resolution Engine

**Base URL**: `http://localhost:8000`  
**Auth**: Bearer JWT in `Authorization: Bearer <token>` header  
**Content-Type**: `application/json` for all requests  
**Timestamps**: ISO 8601 UTC format

---

## Authentication

### POST /auth/register
**Auth Required**: No

**Request**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "name": "John Doe",
  "role": "call_attender"
}
```

**Response 201 — Success**:
```json
{
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "name": "John Doe",
      "role": "call_attender",
      "created_at": "2024-01-15T10:30:00Z"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

**Response 409 — Email Taken**:
```json
{
  "error": {
    "code": "EMAIL_TAKEN",
    "message": "Email already registered"
  }
}
```

**Response 422 — Validation Error**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "fields": {
      "password": "Must be at least 8 characters with uppercase, lowercase, and number",
      "role": "Must be one of: admin, qa, call_attender"
    }
  }
}
```

---

### POST /auth/login
**Auth Required**: No

**Request**:
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response 200 — Success**:
```json
{
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "name": "John Doe",
      "role": "call_attender"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

**Response 401 — Invalid Credentials**:
```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password"
  }
}
```

---

### POST /auth/refresh
**Auth Required**: No (requires valid refresh token)

**Request**:
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**Response 200 — Success**:
```json
{
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }
}
```

**Response 401 — Invalid Token**:
```json
{
  "error": {
    "code": "INVALID_TOKEN",
    "message": "Refresh token is invalid or expired"
  }
}
```

---

### POST /auth/logout
**Auth Required**: Yes

**Request**: Empty body

**Response 200 — Success**:
```json
{
  "data": {
    "message": "Logged out successfully"
  }
}
```

---

## Complaints

### POST /complaints
**Auth Required**: Yes
**Roles**: admin, call_attender

**Request**:
```json
{
  "customer_email": "customer@example.com",
  "customer_name": "Jane Smith",
  "customer_phone": "+91-9876543210",
  "raw_text": "Product stopped working after 2 days",
  "submitted_via": "call"
}
```

**Response 201 — Success**:
```json
{
  "data": {
    "complaint": {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "customer_id": "770e8400-e29b-41d4-a716-446655440002",
      "customer": {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "name": "Jane Smith",
        "email": "customer@example.com",
        "phone": "+91-9876543210"
      },
      "raw_text": "Product stopped working after 2 days",
      "category": "Product",
      "priority": "High",
      "resolution_steps": [
        "1. Verify product warranty status",
        "2. Check for common troubleshooting steps",
        "3. Initiate replacement if under warranty",
        "4. Schedule pickup for defective unit"
      ],
      "sentiment_score": -0.75,
      "status": "open",
      "submitted_via": "call",
      "sla_deadline": "2024-01-15T12:30:00Z",
      "created_at": "2024-01-15T10:30:00Z",
      "resolved_at": null
    }
  }
}
```

**Response 400 — ML Service Unavailable**:
```json
{
  "error": {
    "code": "ML_SERVICE_ERROR",
    "message": "Unable to process complaint. Please try again."
  }
}
```

**Response 422 — Validation Error**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "fields": {
      "raw_text": "Text is required and must be at least 5 characters"
    }
  }
}
```

---

### GET /complaints
**Auth Required**: Yes
**Roles**: admin, qa, call_attender (call_attender sees limited fields)

**Query Parameters**:
- `status` (optional): `open`, `in_progress`, `resolved`, `escalated`
- `category` (optional): `Product`, `Packaging`, `Trade`
- `priority` (optional): `High`, `Medium`, `Low`
- `submitted_via` (optional): `email`, `call`, `dashboard`
- `page` (optional): Default 1
- `limit` (optional): Default 20, max 100
- `search` (optional): Search in raw_text

**Response 200 — Success**:
```json
{
  "data": {
    "complaints": [
      {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "customer": {
          "name": "Jane Smith",
          "email": "customer@example.com"
        },
        "raw_text": "Product stopped working after 2 days",
        "category": "Product",
        "priority": "High",
        "status": "open",
        "sla_deadline": "2024-01-15T12:30:00Z",
        "sla_breached": false,
        "created_at": "2024-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 150,
      "total_pages": 8
    }
  }
}
```

**Call Attender Response** (hides category/priority):
```json
{
  "data": {
    "complaints": [
      {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "customer": {
          "name": "Jane Smith"
        },
        "raw_text": "Product stopped working after 2 days",
        "resolution_steps": [
          "1. Verify product warranty status",
          "2. Check for common troubleshooting steps",
          "3. Initiate replacement if under warranty",
          "4. Schedule pickup for defective unit"
        ],
        "status": "open",
        "created_at": "2024-01-15T10:30:00Z"
      }
    ]
  }
}
```

---

### GET /complaints/:id
**Auth Required**: Yes

**Response 200 — Success**:
```json
{
  "data": {
    "complaint": {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "customer": {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "name": "Jane Smith",
        "email": "customer@example.com",
        "phone": "+91-9876543210"
      },
      "raw_text": "Product stopped working after 2 days",
      "category": "Product",
      "priority": "High",
      "resolution_steps": [
        "1. Verify product warranty status",
        "2. Check for common troubleshooting steps",
        "3. Initiate replacement if under warranty",
        "4. Schedule pickup for defective unit"
      ],
      "sentiment_score": -0.75,
      "status": "open",
      "submitted_via": "call",
      "sla_deadline": "2024-01-15T12:30:00Z",
      "sla_breached": false,
      "created_at": "2024-01-15T10:30:00Z",
      "resolved_at": null,
      "timeline": [
        {
          "id": "880e8400-e29b-41d4-a716-446655440003",
          "action": "complaint_created",
          "performed_by": {
            "name": "John Doe",
            "role": "call_attender"
          },
          "notes": "Complaint received via phone call",
          "created_at": "2024-01-15T10:30:00Z"
        }
      ]
    }
  }
}
```

**Response 404 — Not Found**:
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Complaint not found"
  }
}
```

---

### PATCH /complaints/:id/status
**Auth Required**: Yes
**Roles**: admin, call_attender

**Request**:
```json
{
  "status": "in_progress",
  "notes": "Started troubleshooting with customer"
}
```

**Allowed Status Transitions**:
- `open` → `in_progress`, `resolved`, `escalated`
- `in_progress` → `resolved`, `escalated`
- `escalated` → `in_progress`, `resolved`
- `resolved` → no further transitions

**Response 200 — Success**:
```json
{
  "data": {
    "complaint": {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "status": "in_progress",
      "updated_at": "2024-01-15T11:00:00Z",
      "timeline": [
        {
          "id": "890e8400-e29b-41d4-a716-446655440004",
          "action": "status_changed",
          "performed_by": {
            "name": "John Doe"
          },
          "notes": "Started troubleshooting with customer",
          "created_at": "2024-01-15T11:00:00Z"
        }
      ]
    }
  }
}
```

**Response 400 — Invalid Transition**:
```json
{
  "error": {
    "code": "INVALID_STATUS_TRANSITION",
    "message": "Cannot transition from resolved to in_progress"
  }
}
```

---

### POST /complaints/:id/escalate
**Auth Required**: Yes
**Roles**: admin, call_attender

**Request**:
```json
{
  "reason": "Customer demanding supervisor"
}
```

**Response 200 — Success**:
```json
{
  "data": {
    "complaint": {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "status": "escalated",
      "escalation_reason": "Customer demanding supervisor",
      "escalated_at": "2024-01-15T11:30:00Z"
    }
  }
}
```

---

## Real-Time SSE

### GET /complaints/stream
**Auth Required**: Yes (via query param: `?token=<jwt>`)
**Content-Type**: `text/event-stream`

**SSE Event Format**:
```
event: complaint_update
data: {"type": "new_complaint", "complaint_id": "...", "timestamp": "..."}

event: status_change
data: {"type": "status_changed", "complaint_id": "...", "new_status": "...", "timestamp": "..."}

event: sla_breach
data: {"type": "sla_breach", "complaint_id": "...", "breach_time": "..."}

event: ping
data: {"type": "ping", "timestamp": "..."}
```

**Connection**: Maintains persistent connection, sends heartbeat every 30 seconds.

---

## Email Webhook

### POST /webhooks/email/inbound
**Auth Required**: No (secured by Brevo webhook signature)

**Brevo Payload**:
```json
{
  "event": "inbound",
  "email": {
    "from": "customer@example.com",
    "to": "support@company.com",
    "subject": "Product Issue",
    "text": "My product stopped working after 2 days of use. Order #12345",
    "html": "<p>My product stopped working...</p>"
  }
}
```

**Response 200 — Success**:
```json
{
  "data": {
    "complaint_id": "660e8400-e29b-41d4-a716-446655440001",
    "customer_created": true,
    "message": "Complaint created from email"
  }
}
```

**Response 400 — Invalid Signature**:
```json
{
  "error": {
    "code": "INVALID_SIGNATURE",
    "message": "Webhook signature verification failed"
  }
}
```

---

## Analytics

### GET /analytics/dashboard
**Auth Required**: Yes
**Roles**: admin, qa

**Query Parameters**:
- `start_date` (optional): ISO date
- `end_date` (optional): ISO date

**Response 200 — Success**:
```json
{
  "data": {
    "summary": {
      "total_complaints": 1250,
      "open_complaints": 45,
      "resolved_complaints": 1180,
      "escalated_complaints": 25,
      "avg_resolution_time_hours": 18.5,
      "sla_compliance_rate": 94.2
    },
    "by_category": [
      {"category": "Product", "count": 580, "percentage": 46.4},
      {"category": "Packaging", "count": 420, "percentage": 33.6},
      {"category": "Trade", "count": 250, "percentage": 20.0}
    ],
    "by_priority": [
      {"priority": "High", "count": 180, "percentage": 14.4},
      {"priority": "Medium", "count": 520, "percentage": 41.6},
      {"priority": "Low", "count": 550, "percentage": 44.0}
    ],
    "by_status": [
      {"status": "open", "count": 45},
      {"status": "in_progress", "count": 120},
      {"status": "resolved", "count": 1180},
      {"status": "escalated", "count": 25}
    ],
    "resolution_time_trend": [
      {"date": "2024-01-01", "avg_hours": 20.1},
      {"date": "2024-01-02", "avg_hours": 18.5}
    ],
    "complaints_by_hour": [
      {"hour": 0, "count": 5},
      {"hour": 1, "count": 3}
    ]
  }
}
```

---

### GET /analytics/products
**Auth Required**: Yes
**Roles**: qa, admin

**Query Parameters**:
- `start_date` (optional): ISO date
- `end_date` (optional): ISO date
- `category` (optional): Filter by category

**Response 200 — Success**:
```json
{
  "data": {
    "products": [
      {
        "product_name": "Product A",
        "complaint_count": 150,
        "top_issues": ["Stopped working", "Malfunctioning"],
        "avg_resolution_time": 16.5,
        "category": "Product"
      }
    ]
  }
}
```

---

## Demo Mode

### POST /demo/seed
**Auth Required**: Yes
**Roles**: admin only

**Request**:
```json
{
  "count": 1000
}
```

**Response 200 — Success**:
```json
{
  "data": {
    "seeded_count": 1000,
    "message": "Demo data seeded successfully"
  }
}
```

---

### POST /demo/clear
**Auth Required**: Yes
**Roles**: admin only

**Request**: Empty body

**Response 200 — Success**:
```json
{
  "data": {
    "cleared_count": 1000,
    "message": "Demo data cleared successfully"
  }
}
```

---

## Health Check

### GET /health
**Auth Required**: No

**Response 200 — Success**:
```json
{
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2024-01-15T10:30:00Z",
    "services": {
      "database": "connected",
      "ml_service": "connected"
    }
  }
}
```

---

## Error Response Standard

All error responses follow this structure:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description",
    "details": {} // Optional additional context
  }
}
```

**Common Error Codes**:
- `UNAUTHORIZED` — Missing or invalid token
- `FORBIDDEN` — Valid token but insufficient permissions
- `NOT_FOUND` — Resource doesn't exist
- `VALIDATION_ERROR` — Invalid input data
- `INTERNAL_ERROR` — Server error
- `ML_SERVICE_ERROR` — ML service unavailable
- `RATE_LIMITED` — Too many requests

---

**Version**: 1.0.0  
**Last Updated**: 2024-01-15
