from urllib.parse import urlparse

from fastapi import Request
from fastapi.responses import JSONResponse

from app.config import APP_BASE_URL


SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-Permitted-Cross-Domain-Policies": "none",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://s3.tradingview.com https://www.tradingview.com https://www.googletagmanager.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self' https: wss:; "
        "frame-src https://www.tradingview.com https://s.tradingview.com https://www.tradingview-widget.com; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none'"
    ),
}

CSRF_EXEMPT_PATHS = {"/api/billing/webhook"}
CSRF_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def _same_origin_allowed(request: Request) -> bool:
    if request.url.path in CSRF_EXEMPT_PATHS:
        return True
    if request.method.upper() not in CSRF_METHODS or not request.url.path.startswith("/api/"):
        return True

    origin = request.headers.get("origin") or request.headers.get("referer")
    if not origin:
        return True

    parsed = urlparse(origin)
    if not parsed.scheme or not parsed.netloc:
        return False

    allowed_hosts = {request.url.netloc, urlparse(APP_BASE_URL).netloc}
    return parsed.netloc in allowed_hosts


def _apply_security_headers(response):
    for header, value in SECURITY_HEADERS.items():
        response.headers.setdefault(header, value)
    return response


async def add_security_headers(request: Request, call_next):
    if not _same_origin_allowed(request):
        return _apply_security_headers(JSONResponse({"detail": "Origine de requete refusee"}, status_code=403))

    response = await call_next(request)
    _apply_security_headers(response)
    path = request.url.path
    if path.startswith("/static/"):
        versioned = bool(request.url.query)
        if path.endswith((".js", ".css", ".png", ".jpg", ".jpeg", ".webp", ".avif", ".ico", ".svg", ".json")):
            response.headers["Cache-Control"] = (
                "public, max-age=31536000, immutable"
                if versioned
                else "public, max-age=86400"
            )
    elif response.headers.get("content-type", "").startswith("text/html"):
        response.headers["Cache-Control"] = "no-cache, max-age=0, must-revalidate"
    return response
