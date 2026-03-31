import hmac
import logging
import os

import uvicorn
from app.api.routes import health, public, runs
from app.config import settings
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger("sts2")

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="STS2 Data Collector", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}
PUBLIC_PREFIXES = ("/api/",)


@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    if request.url.path in PUBLIC_PATHS or request.url.path.startswith(PUBLIC_PREFIXES):
        return await call_next(request)

    api_key = request.headers.get("X-API-Key", "")
    if not hmac.compare_digest(api_key, settings.api_key):
        logger.warning("Rejected request with invalid API key to %s", request.url.path)
        return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})

    return await call_next(request)


app.include_router(health.router)
app.include_router(runs.router)
app.include_router(public.router)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)