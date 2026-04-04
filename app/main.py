from fastapi import FastAPI
from app.api.routes import router
from dotenv import load_dotenv

load_dotenv(dotenv_path="app/.env")  # ✅ THIS LINE IS IMPORTANT


def create_app() -> FastAPI:
    app = FastAPI(title="AI Showroom Agent")
    app.include_router(router)
    return app


app = create_app()