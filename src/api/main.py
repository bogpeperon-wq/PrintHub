"""
FastAPI Application - main API entry point.
"""
from fastapi import FastAPI, HealthCheck
from contextlib import asynccontextmanager

from src.utils.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    from src.db.session import init_db
    await init_db()
    yield
    # Shutdown
    pass


app = FastAPI(
    title="Print Hub API",
    description="API for Print Hub Telegram printing service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Print Hub API",
        "version": "1.0.0",
        "docs": "/docs",
    }


# Placeholder endpoints for Print Agent integration
@app.post("/api/agents/register")
async def register_agent():
    """Register a print agent."""
    return {"status": "ok"}


@app.post("/api/agents/heartbeat")
async def agent_heartbeat():
    """Receive agent heartbeat."""
    return {"status": "ok"}


@app.get("/api/jobs/fetch")
async def fetch_job():
    """Fetch next print job for agent."""
    return {"job": None}  # No jobs available


@app.post("/api/jobs/{job_id}/complete")
async def complete_job(job_id: int):
    """Mark job as completed."""
    return {"status": "ok"}


@app.post("/api/jobs/{job_id}/error")
async def job_error(job_id: int):
    """Report job error."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
