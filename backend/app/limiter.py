"""
Shared rate-limiter instance.

Behind nginx, request.client.host is always the nginx container IP.
We read X-Real-IP (set by nginx: proxy_set_header X-Real-IP $remote_addr)
so each real client gets its own counter.
"""
from fastapi import Request
from slowapi import Limiter


def _real_ip(request: Request) -> str:
    return (
        request.headers.get("X-Real-IP")
        or request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or (request.client.host if request.client else "unknown")
    )


limiter = Limiter(key_func=_real_ip)
