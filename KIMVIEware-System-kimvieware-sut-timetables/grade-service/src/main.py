"""
Grade Service
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import grade

app = FastAPI(
    title="KIMVIEware Grade Service",
    description="Grade management with 80+ branches",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(grade.router)

@app.get("/")
async def root():
    return {"service": "grade-service", "status": "healthy", "branches": "80+"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "complexity": "high"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8004)