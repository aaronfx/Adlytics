"""
ADLYTICS Main Application v5.0 - PRODUCTION GRADE
Single Web Service deployment with comprehensive error handling
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import os
import traceback
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create app instance
app = FastAPI(
    title="ADLYTICS",
    description="AI Ad Pre-Validation SaaS v5.0 - Production Grade",
    version="5.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom exception handlers for consistent error responses
def create_error_response(
    status_code: int,
    error_code: str,
    message: str,
    details: dict = None
) -> dict:
    """Create a consistent error response structure"""
    response = {
        "success": False,
        "error": {
            "code": error_code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat()
        }
    }
    if details:
        response["error"]["details"] = details
    return response

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })

    logger.warning(f"Validation error on {request.url.path}: {errors}")

    return JSONResponse(
        status_code=422,
        content=create_error_response(
            status_code=422,
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"errors": errors}
        )
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle standard HTTP exceptions"""
    error_code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        405: "METHOD_NOT_ALLOWED",
        408: "REQUEST_TIMEOUT",
        409: "CONFLICT",
        429: "TOO_MANY_REQUESTS",
        500: "INTERNAL_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE",
        504: "GATEWAY_TIMEOUT"
    }

    error_code = error_code_map.get(exc.status_code, "HTTP_ERROR")

    logger.warning(f"HTTP {exc.status_code} at {request.url.path}: {exc.detail}")

    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            status_code=exc.status_code,
            error_code=error_code,
            message=str(exc.detail)
        )
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global catch-all handler for unexpected errors"""

    # Log the full traceback for debugging
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        extra={
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )

    # Return generic error to client (hide internal details)
    return JSONResponse(
        status_code=500,
        content=create_error_response(
            status_code=500,
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred. Please try again later."
        )
    )

# Import and register API routes BEFORE static files
try:
    from backend.routes.analyze_v5 import router as analyze_router
    app.include_router(analyze_router, prefix="/api", tags=["analysis"])
    logger.info("✅ analyze_router v5 loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load analyze_router: {e}")
    logger.error(traceback.format_exc())

# Health check endpoint (for Render)
@app.get("/health")
async def health_check():
    """Health check for Render and monitoring"""
    return {
        "status": "healthy",
        "version": "5.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "env": {
            "OPENROUTER_API_KEY_SET": bool(os.getenv("OPENROUTER_API_KEY")),
            "PORT": os.getenv("PORT", "10000")
        }
    }

# SPA Static Files Handler
class SPAStaticFiles(StaticFiles):
    """Custom StaticFiles that serves index.html for 404s (SPA support)"""
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except (HTTPException, StarletteHTTPException) as ex:
            if ex.status_code == 404:
                # Serve index.html for any 404 (client-side routing)
                return await super().get_response("index.html", scope)
            else:
                raise ex

# Determine static files path
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if not os.path.exists(frontend_path):
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")

# Mount static files LAST (after all API routes)
if os.path.exists(frontend_path):
    app.mount("/", SPAStaticFiles(directory=frontend_path, html=True), name="spa")
    logger.info(f"✅ Static files mounted from {frontend_path}")
else:
    logger.warning(f"⚠️ Frontend path not found: {frontend_path}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
