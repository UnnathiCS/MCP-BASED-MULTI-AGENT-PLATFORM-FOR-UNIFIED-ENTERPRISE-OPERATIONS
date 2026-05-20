from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.onboarding import router, agent_router

app = FastAPI(
    title="HR Onboarding Agent",
    description="Manages employee onboarding workflows",
    version="1.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)
app.include_router(agent_router)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {
        "name": "HR Onboarding Agent",
        "version": "1.0.0",
        "endpoints": {
            "onboarding": "/onboarding",
            "agent_orchestrate": "/agent/orchestrate",
            "health": "/health"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
