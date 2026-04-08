from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.meetings import router as meetings_router
from app.routes.meetings import agent_router

app = FastAPI(title="Meeting Calendar Agent", version="0.1.0")

app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

app.include_router(meetings_router)
app.include_router(agent_router)


@app.get("/health")
def health():
	return {"status": "ok"}
