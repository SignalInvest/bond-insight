import logging
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


logger = logging.getLogger("bond_insight")


def error_body(code: str, message: str, details: Any = None):
    body = {"error": {"code": code, "message": message}}
    if details is not None:
        body["error"]["details"] = details
    return body


def register_error_handlers(app: FastAPI):
    @app.exception_handler(HTTPException)
    async def http_error_handler(request: Request, exc: HTTPException):
        if isinstance(exc.detail, dict):
            message = exc.detail.get("message", "Request failed")
            details = {key: value for key, value in exc.detail.items() if key != "message"}
        else:
            message = str(exc.detail)
            details = None
        code = {
            404: "NOT_FOUND",
            422: "INVALID_REQUEST",
            503: "SERVICE_UNAVAILABLE",
        }.get(exc.status_code, "HTTP_ERROR")
        return JSONResponse(content=error_body(code, message, details or None), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        details = [
            {"field": ".".join(str(part) for part in error["loc"][1:]), "message": error["msg"]}
            for error in exc.errors()
        ]
        return JSONResponse(
            content=error_body("VALIDATION_ERROR", "Invalid request parameters", details),
            status_code=422,
        )

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception):
        logger.exception("Unhandled API error", exc_info=exc)
        return JSONResponse(
            content=error_body("INTERNAL_ERROR", "An unexpected error occurred"),
            status_code=500,
        )
