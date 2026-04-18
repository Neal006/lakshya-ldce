"""
Shared httpx async client — reuses TCP connections across all agent calls.
Saves ~50-100ms per call vs creating a new AsyncClient each time.
"""

import httpx

_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    """Return a shared AsyncClient. Per-request timeout can be set via timeout= kwarg on individual calls."""
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=30.0)
    return _client
