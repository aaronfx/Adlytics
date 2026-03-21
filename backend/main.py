"""
ADLYTICS - AI Ad Pre-Validation & ROI Simulator
Main FastAPI Application (Single Web Service Deployment)
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from pathlib import Path
import os

# Import API routes
from backend.routes.analyze import router as analyze_router

# Determine static files path - works for both local and Render
current_file = Path(__file__).resolve()
backend_dir = current_file.parent
project_root = backend_dir.parent
static_path = project_root / "frontend"

# Fallback for Render deployment structure
if not static_path.exists():
    static_path = Path("frontend")
if not static_path.exists():
    static_path = Path("/app/frontend")
if not static_path.exists():
    static_path = Path(os.getcwd()) / "frontend"

print(f"Static files path: {static_path} (exists: {static_path.exists()})")

# Custom StaticFiles for SPA support
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

app = FastAPI(
    title="ADLYTICS API",
    description="AI-powered ad pre-validation and ROI simulation",
    version="1.0.0"
)

# CORS - Allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes FIRST (before static files)
app.include_router(analyze_router, prefix="/api", tags=["analysis"])

# Config endpoints
@app.get("/api/audience-config")
async def get_audience_config():
    """Get audience targeting configuration"""
    return {
        "countries": [
            {"code": "nigeria", "name": "Nigeria", "currency": "₦", "regions": ["Lagos", "Abuja", "Port Harcourt", "Kano", "Ibadan"]},
            {"code": "ghana", "name": "Ghana", "currency": "₵", "regions": ["Accra", "Kumasi", "Tamale"]},
            {"code": "kenya", "name": "Kenya", "currency": "KSh", "regions": ["Nairobi", "Mombasa", "Kisumu"]},
            {"code": "south_africa", "name": "South Africa", "currency": "R", "regions": ["Johannesburg", "Cape Town", "Durban"]},
            {"code": "uk", "name": "United Kingdom", "currency": "£", "regions": ["London", "Manchester", "Birmingham", "Glasgow"]},
            {"code": "us", "name": "United States", "currency": "$", "regions": ["New York", "California", "Texas", "Florida", "Illinois"]},
            {"code": "canada", "name": "Canada", "currency": "$", "regions": ["Ontario", "Quebec", "British Columbia", "Alberta"]},
            {"code": "australia", "name": "Australia", "currency": "$", "regions": ["New South Wales", "Victoria", "Queensland"]},
            {"code": "uae", "name": "UAE", "currency": "AED", "regions": ["Dubai", "Abu Dhabi", "Sharjah"]},
            {"code": "india", "name": "India", "currency": "₹", "regions": ["Maharashtra", "Karnataka", "Delhi", "Tamil Nadu"]}
        ],
        "age_brackets": [
            {"value": "18-24", "label": "18-24", "traits": "High mobile usage, TikTok native, price sensitive"},
            {"value": "25-34", "label": "25-34", "traits": "Career building, high purchase intent, social proof driven"},
            {"value": "35-44", "label": "35-44", "traits": "Family focused, value quality over price, research-heavy"},
            {"value": "45-54", "label": "45-54", "traits": "Established income, skeptical of hype, loyalty-driven"},
            {"value": "55-64", "label": "55-64", "traits": "Conservative buyers, prefer established brands"},
            {"value": "65+", "label": "65+", "traits": "Value simplicity, high trust threshold"}
        ],
        "income_levels": [
            {"value": "low", "label": "Low Income", "description": "Price sensitive, seeks deals"},
            {"value": "lower_middle", "label": "Lower Middle", "description": "Budget conscious, value seekers"},
            {"value": "middle", "label": "Middle Income", "description": "Balanced buyers, quality focused"},
            {"value": "upper_middle", "label": "Upper Middle", "description": "Premium preference, less price sensitive"},
            {"value": "high", "label": "High Income", "description": "Luxury oriented, exclusivity matters"}
        ],
        "education_levels": [
            {"value": "secondary", "label": "Secondary School"},
            {"value": "high_school", "label": "High School"},
            {"value": "vocational", "label": "Vocational Training"},
            {"value": "bachelor", "label": "Bachelor's Degree"},
            {"value": "master", "label": "Master's Degree"},
            {"value": "doctorate", "label": "Doctorate/Professional"}
        ],
        "occupations": [
            {"value": "student", "label": "Student", "pain_points": "Limited budget, future anxiety, peer pressure"},
            {"value": "entry_level", "label": "Entry Level Professional", "pain_points": "Career growth, imposter syndrome, work-life balance"},
            {"value": "mid_level", "label": "Mid-Level Professional", "pain_points": "Career plateau, upskilling, time management"},
            {"value": "senior_level", "label": "Senior Professional", "pain_points": "Leadership pressure, legacy building, delegation"},
            {"value": "entrepreneur", "label": "Entrepreneur/Business Owner", "pain_points": "Cash flow, scaling, competition"},
            {"value": "freelancer", "label": "Freelancer/Gig Worker", "pain_points": "Income stability, client acquisition, benefits"},
            {"value": "unemployed", "label": "Unemployed/Job Seeker", "pain_points": "Financial pressure, skill gaps, motivation"},
            {"value": "retired", "label": "Retired", "pain_points": "Fixed income, health costs, legacy"}
        ],
        "psychographics": [
            {"value": "innovators", "label": "Innovators", "traits": "First adopters, risk takers, trendsetters"},
            {"value": "early_adopters", "label": "Early Adopters", "traits": "Opinion leaders, selective adoption, visionaries"},
            {"value": "early_majority", "label": "Early Majority", "traits": "Pragmatists, proven solutions, risk averse"},
            {"value": "late_majority", "label": "Late Majority", "traits": "Skeptics, necessity driven, price sensitive"},
            {"value": "laggards", "label": "Laggards", "traits": "Traditionalists, resistant to change, price focused"}
        ],
        "pain_points": [
            {"value": "financial_pressure", "label": "Financial Pressure", "description": "Struggling with bills, debt, or saving"},
            {"value": "time_scarcity", "label": "Time Scarcity", "description": "Overwhelmed, busy, need efficiency"},
            {"value": "skill_gaps", "label": "Skill/Knowledge Gaps", "description": "Need to learn, feeling behind"},
            {"value": "health_wellness", "label": "Health & Wellness", "description": "Physical/mental health concerns"},
            {"value": "social_status", "label": "Social Status", "description": "Recognition, belonging, status anxiety"},
            {"value": "security_safety", "label": "Security & Safety", "description": "Risk avoidance, protection needs"},
            {"value": "convenience", "label": "Convenience", "description": "Simplification, ease of use"}
        ],
        "tech_savviness": [
            {"value": "low", "label": "Low", "description": "Prefers simple interfaces, needs guidance"},
            {"value": "medium", "label": "Medium (Default)", "description": "Comfortable with common apps"},
            {"value": "high", "label": "High", "description": "Early adopter, prefers advanced features"}
        ],
        "purchase_styles": [
            {"value": "impulse", "label": "Impulse Buyer", "description": "Quick decisions, emotional triggers"},
            {"value": "researcher", "label": "Thorough Researcher", "description": "Compares options, reads reviews"},
            {"value": "loyal", "label": "Brand Loyal", "description": "Sticks to trusted brands"},
            {"value": "bargain", "label": "Bargain Hunter", "description": "Price focused, seeks deals"}
        ]
    }

@app.get("/api/platforms")
async def get_platforms():
    """Get supported platforms"""
    return {
        "platforms": [
            {"id": "tiktok", "name": "TikTok"},
            {"id": "instagram", "name": "Instagram"},
            {"id": "facebook", "name": "Facebook"},
            {"id": "youtube", "name": "YouTube"},
            {"id": "twitter", "name": "Twitter/X"},
            {"id": "linkedin", "name": "LinkedIn"},
            {"id": "google", "name": "Google Ads"},
            {"id": "snapchat", "name": "Snapchat"}
        ]
    }

@app.get("/api/industries")
async def get_industries():
    """Get supported industries"""
    return {
        "industries": [
            {"id": "forex", "name": "Forex Trading"},
            {"id": "crypto", "name": "Cryptocurrency"},
            {"id": "ecommerce", "name": "E-commerce"},
            {"id": "saas", "name": "SaaS/Software"},
            {"id": "education", "name": "Education"},
            {"id": "health", "name": "Health & Wellness"},
            {"id": "finance", "name": "Finance/Banking"},
            {"id": "realestate", "name": "Real Estate"},
            {"id": "fashion", "name": "Fashion/Apparel"},
            {"id": "food", "name": "Food & Beverage"},
            {"id": "travel", "name": "Travel & Hospitality"},
            {"id": "gaming", "name": "Gaming"},
            {"id": "other", "name": "Other"}
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ADLYTICS API"}

# Mount static files LAST with SPA support
if static_path.exists():
    app.mount("/", SPAStaticFiles(directory=str(static_path), html=True), name="spa")
else:
    print(f"WARNING: Static files not found at {static_path}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
