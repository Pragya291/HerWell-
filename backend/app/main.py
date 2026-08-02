import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .routers import auth, cycles, mood, fitness, health, wellness

# Create SQLite database tables if they do not exist
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HerWellness Hub API",
    description="Backend API for Women's Health & Wellness Web Application",
    version="1.0.0"
)

# Enable CORS for local development and demoing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(auth.router)
app.include_router(cycles.router)
app.include_router(mood.router)
app.include_router(fitness.router)
app.include_router(health.router)
app.include_router(wellness.router)


@app.get("/api/health")
def health_check():
    """Health check endpoint to verify backend service status."""
    return {"status": "online", "message": "HerWellness API is running smoothly."}


# Serve SPA static files (HTML, CSS, JS) from static folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
