import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .routers import auth, cycles, mood, fitness, health, wellness

# Create SQLite database tables if they do not exist
Base.metadata.create_all(bind=engine)

# Run schema migrations to add new columns to cycle_logs and users if they don't exist
from sqlalchemy import inspect, text
inspector = inspect(engine)

# Migration for cycle_logs table
existing_cycle_cols = [col['name'] for col in inspector.get_columns('cycle_logs')]
new_cycle_cols = {
    "cramps_severity": "INTEGER",
    "headache_severity": "INTEGER",
    "acne_severity": "INTEGER",
    "breast_tenderness_severity": "INTEGER",
    "hair_loss_severity": "INTEGER",
    "hirsutism_severity": "INTEGER",
    "ovulation_test_result": "VARCHAR"
}
with engine.connect() as conn:
    for col_name, col_type in new_cycle_cols.items():
        if col_name not in existing_cycle_cols:
            try:
                conn.execute(text(f"ALTER TABLE cycle_logs ADD COLUMN {col_name} {col_type} NULL"))
                conn.commit()
            except Exception as e:
                print(f"Migration error adding {col_name} to cycle_logs: {e}")

# Migration for users table
existing_user_cols = [col['name'] for col in inspector.get_columns('users')]
new_user_cols = {
    "tracking_mode": "VARCHAR DEFAULT 'regular'",
    "custom_cycle_length": "INTEGER"
}
with engine.connect() as conn:
    for col_name, col_type in new_user_cols.items():
        if col_name not in existing_user_cols:
            try:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception as e:
                print(f"Migration error adding {col_name} to users: {e}")


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
