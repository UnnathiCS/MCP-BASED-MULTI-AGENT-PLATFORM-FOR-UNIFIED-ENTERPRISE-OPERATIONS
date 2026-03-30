from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(title="Enterprise Document Review Agent")

app.include_router(router)
