from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from app.api.routes import router


env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(env_path)


def create_app() -> FastAPI:
    app = FastAPI(title="AI Showroom Agent")
    app.include_router(router)
    return app


app = create_app()