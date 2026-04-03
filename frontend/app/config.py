import os


class Config:
    USE_LOCAL_HOST = False
    API_BASE_URL = (
        "http://localhost:8080"
        if USE_LOCAL_HOST
        else "https://sts2-data-collector-production.up.railway.app"
    )
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
