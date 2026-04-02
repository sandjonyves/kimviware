"""
Room Service - FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import room

app = FastAPI(
    title="KIMVIEware Room Service",
    description="Room booking microservice",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(room.router)

@app.get("/")
async def root():
    return {"service": "room-service", "status": "healthy", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "database": "connected",
        "services": {
            "room_management": "operational",
            "booking": "operational"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
