"""
ADLYTICS v6.1 main.py — mounts ALL routers
Drop-in replacement for your existing main.py.
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import os, logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ADLYTICS", version="6.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# ── Health ─────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "healthy", "version": "6.1.0", "timestamp": datetime.now().isoformat()}

@app.get("/api/test")
async def api_test():
    return {"message": "API working", "version": "6.1.0"}

@app.options("/api/analyze")
async def analyze_options():
    return JSONResponse(
        content={"message": "OK"},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

# ── Core analysis router ───────────────────────────────────────
try:
    from backend.routes.analyze import router as analyze_router
    app.include_router(analyze_router, prefix="/api")
    logger.info("✅ analyze router mounted")
except Exception as e:
    logger.error(f"❌ analyze router failed: {e}")
    @app.post("/api/analyze")
    async def analyze_fallback():
        raise HTTPException(status_code=503, detail=f"Analyze router unavailable: {e}")

# ── Rewrite engine ─────────────────────────────────────────────
try:
    from backend.routes.rewrite_engine import router as rewrite_router
    app.include_router(rewrite_router, prefix="/api")
    logger.info("✅ rewrite router mounted")
except Exception as e:
    logger.warning(f"⚠️ rewrite router: {e}")

# ── Hook library ───────────────────────────────────────────────
try:
    from backend.routes.hooks_library import router as hooks_router
    app.include_router(hooks_router, prefix="/api")
    logger.info("✅ hooks router mounted")
except Exception as e:
    logger.warning(f"⚠️ hooks router: {e}")

# ── Tier 2 (compliance, psychographic, storyboard, benchmarks, AB, landing) ──
try:
    from backend.routes.tier2_routes import router as tier2_router
    app.include_router(tier2_router, prefix="/api")
    logger.info("✅ tier2 router mounted")
except Exception as e:
    logger.warning(f"⚠️ tier2 router: {e}")

# ── Static files / SPA ─────────────────────────────────────────
frontend_paths = [
    os.path.join(os.path.dirname(__file__), "..", "frontend"),
    os.path.join(os.path.dirname(__file__), "..", "..", "frontend"),
    os.path.join(os.getcwd(), "frontend"),
    "/opt/render/project/src/frontend",
]
frontend_path = next((p for p in frontend_paths if os.path.exists(p)), None)

if frontend_path:
    logger.info(f"✅ Static files from: {frontend_path}")
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/", response_class=HTMLResponse)
    async def serve_root():
        try:
            with open(os.path.join(frontend_path, "app.html")) as f:
                return f.read()
        except Exception:
            return "<h1>ADLYTICS v6.1</h1>"

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
            return f"<h1>{path} — not found</h1>"
else:
    logger.warning("⚠️ No frontend directory found")

    @app.get("/")
    async def root():
        return {"message": "ADLYTICS API v6.1", "status": "running"}

logger.info("🚀 ADLYTICS v6.1 startup complete")
