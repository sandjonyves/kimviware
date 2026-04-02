"""
Timetable Service
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import timetable

app = FastAPI(
    title="KIMVIEware Timetable Service",
    description="Course scheduling with 500+ branches",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(timetable.router)

@app.get("/")
async def root():
    return {"service": "timetable-service", "status": "healthy", "branches": "500+"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "complexity": "extreme"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)