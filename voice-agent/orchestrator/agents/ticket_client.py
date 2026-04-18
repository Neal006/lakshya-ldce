import httpx
import time
import logging
from config import BACKEND_SERVICE_URL, SERVICE_ACCOUNT_EMAIL, SERVICE_ACCOUNT_PASSWORD
from agents.http_pool import get_client

logger = logging.getLogger(__name__)

_token_cache: dict = {"token": None, "expires": 0}


async def _ensure_service_account() -> bool:
    """Register the service account if it doesn't exist, then login."""
    try:
        client = get_client()
        # Try to register (may fail if already exists, that's OK)
        await client.post(
            f"{BACKEND_SERVICE_URL}/auth/register",
            json={
                "email": SERVICE_ACCOUNT_EMAIL,
                "password": SERVICE_ACCOUNT_PASSWORD,
                "name": "Voice System",
                "role": "admin",
            },
            timeout=10.0,
        )
        # Now login
        response = await client.post(
            f"{BACKEND_SERVICE_URL}/auth/login",
            json={
                "email": SERVICE_ACCOUNT_EMAIL,
                "password": SERVICE_ACCOUNT_PASSWORD,
            },
            timeout=10.0,
        )
        response.raise_for_status()
        data = response.json()
        token = data.get("data", {}).get("access_token") or data.get("access_token")
        if token:
            _token_cache["token"] = token
            _token_cache["expires"] = time.time() + 1800  # 30 min cache
            return True
    except Exception as e:
        logger.error(f"Service account auth failed: {e}")
    return False


async def _get_auth_token() -> str | None:
    """Get a valid auth token, refreshing if needed."""
    if _token_cache["token"] and _token_cache["expires"] > time.time():
        return _token_cache["token"]

    if await _ensure_service_account():
        return _token_cache["token"]
    return None


async def create_ticket(
    raw_text: str,
    category: str,
    priority: str,
    sentiment_score: float,
    resolution_steps: list,
    customer_name: str = "Voice Caller",
    customer_phone: str = "",
    customer_email: str = "",
) -> dict | None:
    """Create a ticket via the existing backend API."""
    if not customer_email:
        customer_email = f"voice_{customer_phone or 'unknown'}@call.lakshya"

    # Ensure customer_name is not empty (backend requires min_length=1)
    if not customer_name or not customer_name.strip():
        customer_name = "Voice Caller"

    # Normalize resolution steps to list of strings
    normalized_steps = [str(step) for step in resolution_steps]

    payload = {
        "customer_email": customer_email,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "raw_text": raw_text,
        "submitted_via": "voice",
    }

    token = await _get_auth_token()
    if not token:
        logger.error("Failed to get auth token for ticket creation")
        return None

    try:
        client = get_client()
        response = await client.post(
            f"{BACKEND_SERVICE_URL}/complaints",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=15.0,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("data", {}).get("complaint", data.get("data"))
    except httpx.HTTPStatusError as e:
        logger.error(f"Ticket creation HTTP error: {e.response.status_code} - {e.response.text[:200]}")
    except Exception as e:
        logger.error(f"Ticket creation error: {e}")

    return None
