"""
ADLYTICS Analysis Route v4.1 - COMPATIBLE VERSION
Uses existing get_ai_engine() API structure
"""

from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from typing import Optional, List
import os

# Import using existing API structure
from backend.services.ai_engine import get_ai_engine
from backend.services.media_processor import process_media

router = APIRouter()

# Get AI engine instance (singleton pattern)
ai_engine = get_ai_engine()


@router.post("/analyze")
async def analyze_endpoint(
    ad_copy: Optional[str] = Form(None),
    video_script: Optional[str] = Form(None),
    platform: str = Form(...),
    audience_country: str = Form(...),
    audience_age: str = Form(...),
    industry: str = Form(...),
    objective: str = Form("conversions"),
    audience_region: Optional[str] = Form(None),
    audience_gender: Optional[str] = Form(None),
    audience_income: Optional[str] = Form(None),
    audience_education: Optional[str] = Form(None),
    audience_occupation: Optional[str] = Form(None),
    audience_psychographic: Optional[str] = Form(None),
    audience_pain_point: Optional[str] = Form(None),
    tech_savviness: Optional[str] = Form(None),
    purchase_behavior: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None)
):
    """
    Main analysis endpoint - v4.1
    Supports ad copy, video script, or both
    """

    try:
        # Build request data
        request_data = {
            "ad_copy": ad_copy or "",
            "video_script": video_script or "",
            "platform": platform,
            "audience_country": audience_country,
            "audience_age": audience_age,
            "industry": industry,
            "objective": objective,
            "audience_region": audience_region,
            "audience_gender": audience_gender,
            "audience_income": audience_income,
            "audience_education": audience_education,
            "audience_occupation": audience_occupation,
            "audience_psychographic": audience_psychographic,
            "audience_pain_point": audience_pain_point,
            "tech_savviness": tech_savviness,
            "purchase_behavior": purchase_behavior
        }

        # Validate at least one content type is provided
        content_mode = ai_engine.detect_content_mode(request_data)

        if content_mode == "adCopy" and not ad_copy:
            raise HTTPException(status_code=400, detail="Ad copy is required for ad copy mode")
        if content_mode == "videoScript" and not video_script:
            raise HTTPException(status_code=400, detail="Video script is required for video script mode")

        # Process media files if provided
        files = []
        if image:
            image_data = await process_media(image, "image")
            files.append(image_data)
        if video:
            video_data = await process_media(video, "video")
            files.append(video_data)

        # Run analysis using AI engine
        result = await ai_engine.analyze(request_data, files)

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/audience-config")
async def get_audience_config():
    """Return audience targeting configuration"""
    return {
        "countries": [
            {
                "code": "nigeria",
                "name": "Nigeria",
                "currency": "₦",
                "regions": ["Lagos", "Abuja", "Port Harcourt", "Ibadan", "Kano"]
            },
            {
                "code": "us",
                "name": "United States",
                "currency": "$",
                "regions": ["New York", "California", "Texas", "Florida", "Illinois"]
            },
            {
                "code": "uk",
                "name": "United Kingdom",
                "currency": "£",
                "regions": ["London", "Manchester", "Birmingham", "Glasgow"]
            },
            {
                "code": "canada",
                "name": "Canada",
                "currency": "C$",
                "regions": ["Toronto", "Vancouver", "Montreal", "Calgary"]
            },
            {
                "code": "australia",
                "name": "Australia",
                "currency": "A$",
                "regions": ["Sydney", "Melbourne", "Brisbane", "Perth"]
            },
            {
                "code": "ghana",
                "name": "Ghana",
                "currency": "₵",
                "regions": ["Accra", "Kumasi", "Tamale"]
            },
            {
                "code": "kenya",
                "name": "Kenya",
                "currency": "KSh",
                "regions": ["Nairobi", "Mombasa", "Kisumu"]
            },
            {
                "code": "south_africa",
                "name": "South Africa",
                "currency": "R",
                "regions": ["Johannesburg", "Cape Town", "Durban", "Pretoria"]
            },
            {
                "code": "india",
                "name": "India",
                "currency": "₹",
                "regions": ["Mumbai", "Delhi", "Bangalore", "Hyderabad", "Chennai"]
            },
            {
                "code": "uae",
                "name": "United Arab Emirates",
                "currency": "AED",
                "regions": ["Dubai", "Abu Dhabi", "Sharjah"]
            }
        ],
        "age_brackets": [
            {"value": "18-24", "label": "18-24 (Gen Z)", "traits": "Digital natives, authenticity-focused, short attention spans"},
            {"value": "25-34", "label": "25-34 (Millennials)", "traits": "Career growth, lifestyle balance, value-conscious"},
            {"value": "35-44", "label": "35-44 (Young Gen X/Millennials)", "traits": "Family-focused, stability-seeking, quality over price"},
            {"value": "45-54", "label": "45-54 (Gen X)", "traits": "Wealth accumulation, health-conscious, skeptical"},
            {"value": "55-64", "label": "55-64 (Boomers/Gen X)", "traits": "Retirement planning, simplicity preferred, loyal"},
            {"value": "65+", "label": "65+ (Seniors)", "traits": "Security-focused, simple language, trust paramount"}
        ],
        "income_levels": [
            {"value": "low", "label": "Low Income", "description": "Price sensitive, deals-focused, budget constraints"},
            {"value": "lower_middle", "label": "Lower Middle", "description": "Value seekers, occasional splurges, practical"},
            {"value": "middle", "label": "Middle Income", "description": "Balanced approach, quality matters, some flexibility"},
            {"value": "upper_middle", "label": "Upper Middle", "description": "Quality focused, brand conscious, convenience premium"},
            {"value": "high", "label": "High Income", "description": "Premium preference, time value, exclusivity"},
            {"value": "very_high", "label": "Very High", "description": "Luxury-focused, status conscious, bespoke service"}
        ],
        "education_levels": [
            {"value": "high_school", "label": "High School"},
            {"value": "some_college", "label": "Some College"},
            {"value": "bachelors", "label": "Bachelor's Degree"},
            {"value": "graduate", "label": "Graduate Degree"},
            {"value": "professional", "label": "Professional Degree"},
            {"value": "doctorate", "label": "Doctorate"}
        ],
        "occupations": [
            {"value": "student", "label": "Student", "pain_points": "Budget constraints, time pressure, future anxiety"},
            {"value": "entry_level", "label": "Entry Level Professional", "pain_points": "Career growth, skill building, proving worth"},
            {"value": "mid_level", "label": "Mid-Level Professional", "pain_points": "Work-life balance, career plateau, skill updating"},
            {"value": "senior_professional", "label": "Senior Professional", "pain_points": "Leadership pressure, legacy building, staying relevant"},
            {"value": "entrepreneur", "label": "Entrepreneur/Business Owner", "pain_points": "Cash flow, growth, competition, time management"},
            {"value": "freelancer", "label": "Freelancer/Creative", "pain_points": "Income stability, client acquisition, admin burden"},
            {"value": "homemaker", "label": "Homemaker/Parent", "pain_points": "Time scarcity, household management, self-care neglect"},
            {"value": "retired", "label": "Retired", "pain_points": "Fixed income, health, purpose, technology gap"}
        ],
        "psychographics": [
            {"value": "value_seeker", "label": "Value Seeker", "traits": "Price-conscious, deal hunter, practical"},
            {"value": "quality_focused", "label": "Quality Focused", "traits": "Premium preference, durability matters, research-heavy"},
            {"value": "convenience_seeker", "label": "Convenience Seeker", "traits": "Time-poor, frictionless experience, speed matters"},
            {"value": "status_seeker", "label": "Status Seeker", "traits": "Brand conscious, social signaling, exclusivity"},
            {"value": "risk_averse", "label": "Risk Averse", "traits": "Safety first, guarantees needed, proven solutions"}
        ],
        "pain_points": [
            {"value": "financial_stress", "label": "Financial Stress", "description": "Money worries, debt, insufficient savings"},
            {"value": "time_scarcity", "label": "Time Scarcity", "description": "Overwhelmed, too busy, work-life imbalance"},
            {"value": "health_concerns", "label": "Health Concerns", "description": "Physical/mental health, fitness, wellness"},
            {"value": "career_stagnation", "label": "Career Stagnation", "description": "No growth, skill gaps, job insecurity"},
            {"value": "relationship_issues", "label": "Relationship Issues", "description": "Family, romantic, social connection problems"},
            {"value": "lack_of_confidence", "label": "Lack of Confidence", "description": "Self-doubt, imposter syndrome, fear of failure"},
            {"value": "information_overload", "label": "Information Overload", "description": "Too many options, decision paralysis, complexity"}
        ]
    }


@router.get("/platforms")
async def get_platforms():
    """Return supported platforms"""
    return {
        "platforms": [
            {"id": "facebook", "name": "Facebook"},
            {"id": "instagram", "name": "Instagram"},
            {"id": "tiktok", "name": "TikTok"},
            {"id": "google", "name": "Google Ads"},
            {"id": "linkedin", "name": "LinkedIn"},
            {"id": "twitter", "name": "Twitter/X"},
            {"id": "youtube", "name": "YouTube"}
        ]
    }


@router.get("/industries")
async def get_industries():
    """Return supported industries"""
    return {
        "industries": [
            {"id": "ecommerce", "name": "E-commerce/Retail"},
            {"id": "saas", "name": "SaaS/Software"},
            {"id": "finance", "name": "Finance/Fintech"},
            {"id": "health", "name": "Health/Wellness"},
            {"id": "education", "name": "Education/Courses"},
            {"id": "realestate", "name": "Real Estate"},
            {"id": "consulting", "name": "Consulting/Agency"},
            {"id": "food", "name": "Food/Beverage"},
            {"id": "fashion", "name": "Fashion/Apparel"},
            {"id": "travel", "name": "Travel/Hospitality"},
            {"id": "tech", "name": "Technology"},
            {"id": "beauty", "name": "Beauty/Personal Care"},
            {"id": "fitness", "name": "Fitness/Sports"},
            {"id": "b2b", "name": "B2B Services"},
            {"id": "nonprofit", "name": "Non-profit"}
        ]
    }
