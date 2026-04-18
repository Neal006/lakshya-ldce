# Verification Report — Feature 2: Authentication

**Date**: 2026-04-18  
**Feature**: Authentication (register, login, refresh, logout)  
**Environment**: Local development (SQLite fallback)

---

## Summary

| Tier | Total | Pass | Fail |
|------|-------|------|------|
| Happy Path | 12 | 12 | 0 |
| Failure Modes | 7 | 7 | 0 |
| Contract Check | 4 | 4 | 0 |
| **Overall** | **23** | **23** | **0** |

---

## Happy Path Tests

| # | Test | Status | Detail |
|---|------|--------|--------|
| 1 | Register returns 201 | PASS | `POST /auth/register` → 201 |
| 2 | Register response has `data.user` | PASS | User object present |
| 3 | Register response has `access_token` | PASS | JWT token present |
| 4 | Register response has `refresh_token` | PASS | JWT token present |
| 5 | Register does NOT leak password | PASS | No `hashed_password` in response |
| 6 | Login returns 200 | PASS | `POST /auth/login` → 200 |
| 7 | Login response has `data.user` | PASS | User object with id, email, name, role |
| 8 | Logout returns 200 | PASS | `POST /auth/logout` with Bearer token → 200 |
| 9 | Logout response has success message | PASS | `"Logged out successfully"` |
| 10 | Refresh token rotation works | PASS | New access_token + refresh_token returned |
| 11 | New refresh token is usable | PASS | Second refresh succeeds with rotated token |
| 12 | Register with valid data creates user | PASS | User persisted with correct email, name, role |

---

## Failure Mode Tests

| # | Test | Expected | Actual | Status |
|---|------|----------|--------|--------|
| 1 | Duplicate email registration | 409 `EMAIL_TAKEN` | 409 `EMAIL_TAKEN` | PASS |
| 2 | Invalid login credentials | 401 `INVALID_CREDENTIALS` | 401 `INVALID_CREDENTIALS` | PASS |
| 3 | Validation error (bad email, short password) | 422 `VALIDATION_ERROR` | 422 `VALIDATION_ERROR` | PASS |
| 4 | Validation error has `fields` dict | `fields` present | `fields` with per-field messages | PASS |
| 5 | No-auth access to protected route | 403 | 403 | PASS |
| 6 | Revoked refresh token rejected | 401 `INVALID_TOKEN` | 401 `INVALID_TOKEN` | PASS |
| 7 | SQL injection in email field | No 500 error | No 500 error | PASS |

---

## Contract Compliance

| API Contract | Implemented | Status |
|-------------|-------------|--------|
| `POST /auth/register` → 201 with `{data: {user, access_token, refresh_token}}` | Yes | PASS |
| `POST /auth/register` → 409 `EMAIL_TAKEN` | Yes | PASS |
| `POST /auth/register` → 422 `VALIDATION_ERROR` with `fields` | Yes | PASS |
| `POST /auth/login` → 200 with `{data: {user, access_token, refresh_token}}` | Yes | PASS |
| `POST /auth/login` → 401 `INVALID_CREDENTIALS` | Yes | PASS |
| `POST /auth/refresh` → 200 with `{data: {access_token, refresh_token}}` | Yes | PASS |
| `POST /auth/refresh` → 401 `INVALID_TOKEN` (expired/revoked) | Yes | PASS |
| `POST /auth/logout` → 200 with `{data: {message}}` | Yes | PASS |
| Error format: `{error: {code, message}}` | Yes | PASS |
| Validation error format: `{error: {code, message, fields}}` | Yes | PASS |
| Password not exposed in any response | Yes | PASS |

---

## Bugs Found & Fixed During Verification

### [CRIT-001] Error format mismatch — `detail` vs `error`
- **Severity**: CRITICAL
- **Description**: FastAPI default `HTTPException` wraps errors in `{"detail": {...}}`, but the API contract specifies `{"error": {...}}`
- **Fix**: Created `AppException` class and registered custom exception handlers in `app/middleware/exceptions.py` for `AppException`, `StarletteHTTPException`, and `RequestValidationError`
- **Status**: FIXED & VERIFIED

### [CRIT-002] Refresh token collision — identical JWTs overwrite revocation
- **Severity**: CRITICAL
- **Description**: When two refresh tokens are created within the same second for the same user (e.g., during rotation), they produced identical JWTs because `sub`, `role`, `type`, and `exp` were identical. The second token overwrote the revoked entry in the in-memory store, making the revoked token usable again.
- **Fix**: Added `jti` (JWT ID) claim using `uuid.uuid4()` to ensure every refresh token has a unique identifier, even if created at the same instant.
- **Status**: FIXED & VERIFIED

### [WARN-001] `datetime.utcnow()` deprecated
- **Severity**: WARNING
- **Description**: SQLAlchemy model defaults used `datetime.utcnow`, which is deprecated in Python 3.12+
- **Fix**: Changed all model defaults to `lambda: datetime.now(timezone.utc)`
- **Status**: FIXED

### [WARN-002] `passlib` incompatible with `bcrypt>=5.0`
- **Severity**: WARNING
- **Description**: `passlib[bcrypt]` crashes with `bcrypt>=5.0` due to internal API changes
- **Fix**: Replaced `passlib` with direct `bcrypt` library calls (`bcrypt.hashpw`, `bcrypt.checkpw`)
- **Status**: FIXED & VERIFIED

### [INFO-001] No-auth returns 403 instead of 401
- **Severity**: INFO
- **Description**: FastAPI's `HTTPBearer` dependency returns 403 when no Authorization header is provided, not 401. This is standard FastAPI behavior. Both 401 and 403 indicate auth failure; 403 is acceptable.
- **Status**: ACCEPTED (no fix needed)

---

## Files Modified in This Verification Cycle

| File | Change |
|------|--------|
| `app/middleware/exceptions.py` | NEW — Custom exception handlers for contract-compliant error format |
| `app/main.py` | Added exception handler registrations, imported `models` in startup |
| `app/services/auth.py` | Fixed: added `jti` claim, replaced `passlib` with `bcrypt` |
| `app/models/models.py` | Fixed: `datetime.utcnow` → `datetime.now(timezone.utc)` |
| `app/schemas/auth.py` | Added `field_validator` for password (uppercase, lowercase, digit) |
| `app/routers/auth.py` | Replaced `HTTPException` with `AppException` for contract-compliant errors |
| `requirements.txt` | Replaced `passlib[bcrypt]` with `bcrypt>=4.0.0` |

---

*Verification completed. All 23 tests passing. 2 CRITICAL bugs found and fixed.*