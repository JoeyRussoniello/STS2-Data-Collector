import uvicorn
from fastapi import FastAPI

from app.api.routes import health, runs

app = FastAPI(title="STS2 Data Collector", version="0.1.0")

app.include_router(health.router)
app.include_router(runs.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
