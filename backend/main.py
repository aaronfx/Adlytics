"""
ADLYTICS v6.0 - FIXED main.py
Critical fix: removed inline /api/analyze that was silently blocking the router route.
In FastAPI, first-registered route wins. The old inline route meant analyze.py was NEVER called.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ADLYTICS", version="6.0.0")

# CORS — must be before ALL routes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# ── Health / test ──────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "6.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/test")
async def api_test():
    return {"message": "API working", "version": "6.0.0"}

# ── Explicit OPTIONS preflight for /api/analyze ────────────────────────────
@app.options("/api/analyze")
async def analyze_options():
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

# ── Mount the real router BEFORE static files ──────────────────────────────
# IMPORTANT: Do NOT define any inline @app.post("/api/analyze") here.
# FastAPI registers routes in order — first match wins.
# The router below owns /api/analyze, /api/audience-config, /api/platforms, /api/industries.
try:
    from backend.routes.analyze import router as analyze_router
    app.include_router(analyze_router, prefix="/api")
    logger.info("✅ analyze router mounted at /api")
except Exception as e:
    logger.error(f"❌ Could not load analyze router: {e}")
    # Emergency fallback — surface the real error, never swallow it silently
    @app.post("/api/analyze")
    async def analyze_fallback():
        raise HTTPException(
            status_code=503,
            detail=f"Analyze router failed to load: {e}"
        )

# ── Static files (LAST — SPA catch-all must not interfere with API) ─────────
frontend_paths = [
    os.path.join(os.path.dirname(__file__), "..", "frontend"),
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend"),
    os.path.join(os.getcwd(), "frontend"),
    "/opt/render/project/src/frontend",
]

frontend_path = next((p for p in frontend_paths if os.path.exists(p)), None)

if frontend_path:
    logger.info(f"✅ Serving static files from: {frontend_path}")
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def serve_root():
        try:
            with open(os.path.join(frontend_path, "app.html")) as f:
                return f.read()
        except Exception:
            return "<h1>ADLYTICS v6.0</h1><p>Frontend not found</p>"

    @app.get("/app.html", response_class=HTMLResponse)
    async def serve_app():
        try:
            with open(os.path.join(frontend_path, "app.html")) as f:
                return f.read()
        except Exception:
            return "<h1>Frontend not found</h1>"

    @app.get("/{path:path}", response_class=HTMLResponse)
    async def serve_spa(path: str):
        if path.startswith("api/") or path in ["docs", "redoc", "openapi.json", "health"]:
            raise HTTPException(status_code=404, detail="Not found")
        try:
            with open(os.path.join(frontend_path, "app.html")) as f:
                return f.read()
        except Exception:
            return f"<h1>{path}</h1><p>Not found</p>"
else:
    logger.warning("⚠️ No frontend directory found")

    @app.get("/")
    async def root():
        return {"message": "ADLYTICS API v6.0", "status": "running"}

logger.info("🚀 ADLYTICS v6.0 startup complete")
