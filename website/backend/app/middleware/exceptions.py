from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


class AppException(Exception):
    def __init__(self, status_code: int, code: str, message: str, fields: dict | None = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.fields = fields


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    error_body = {"code": exc.code, "message": exc.message}
    if exc.fields:
        error_body["fields"] = exc.fields
    return JSONResponse(status_code=exc.status_code, content={"error": error_body})


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": "INTERNAL_ERROR", "message": str(exc.detail)}})


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    fields = {}
    for error in exc.errors():
        field_name = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        if field_name:
            fields[field_name] = error["msg"]
    
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid input data",
                "fields": fields,
            }
        },
    )