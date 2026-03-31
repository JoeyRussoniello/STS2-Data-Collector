import hmac

import uvicorn
from app.api.routes import health, runs
from app.config import settings
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="STS2 Data Collector", version="0.1.0")

# Paths that don't require an API key
PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


@app.middleware("http")
async def verify_api_key(request: Request, call_next):
    if request.url.path in PUBLIC_PATHS:
        return await call_next(request)

    api_key = request.headers.get("X-API-Key", "")
    if not hmac.compare_digest(api_key, settings.api_key):
        return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})

    return await call_next(request)


app.include_router(health.router)
app.include_router(runs.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
