"""
ADLYTICS - Analyze API Route with Enhanced Audience Targeting
Main endpoint for ad analysis with detailed demographic options
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional, List
import json
from pydantic import BaseModel

from backend.services.ai_engine import AIEngine
from backend.services.media_processor import MediaProcessor

router = APIRouter()
ai_engine = AIEngine()
media_processor = MediaProcessor()

# Audience configuration data
AUDIENCE_CONFIG = {
    "countries": [
        {"code": "NG", "name": "Nigeria", "currency": "₦", "regions": ["Lagos", "Abuja", "Kano", "Ibadan", "Port Harcourt", "Benin City", "Kaduna", "Enugu", "Onitsha", "Aba"]},
        {"code": "US", "name": "United States", "currency": "$", "regions": ["California", "Texas", "New York", "Florida", "Illinois", "Pennsylvania", "Ohio", "Georgia", "Michigan", "North Carolina"]},
        {"code": "GB", "name": "United Kingdom", "currency": "£", "regions": ["London", "Manchester", "Birmingham", "Leeds", "Glasgow", "Sheffield", "Liverpool", "Bristol", "Edinburgh", "Cardiff"]},
        {"code": "CA", "name": "Canada", "currency": "C$", "regions": ["Ontario", "Quebec", "British Columbia", "Alberta", "Manitoba", "Saskatchewan", "Nova Scotia", "New Brunswick", "Newfoundland", "PEI"]},
        {"code": "AU", "name": "Australia", "currency": "A$", "regions": ["New South Wales", "Victoria", "Queensland", "Western Australia", "South Australia", "Tasmania", "ACT", "Northern Territory"]},
        {"code": "ZA", "name": "South Africa", "currency": "R", "regions": ["Gauteng", "Western Cape", "KwaZulu-Natal", "Eastern Cape", "Free State", "Mpumalanga", "Limpopo", "North West", "Northern Cape"]},
        {"code": "GH", "name": "Ghana", "currency": "₵", "regions": ["Greater Accra", "Ashanti", "Western", "Eastern", "Central", "Northern", "Upper East", "Upper West", "Volta", "Bono"]},
        {"code": "KE", "name": "Kenya", "currency": "KSh", "regions": ["Nairobi", "Mombasa", "Kisumu", "Nakuru", "Eldoret", "Kiambu", "Machakos", "Kajiado", "Nyeri", "Meru"]},
        {"code": "IN", "name": "India", "currency": "₹", "regions": ["Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Telangana", "Gujarat", "West Bengal", "Rajasthan", "Uttar Pradesh", "Kerala"]},
        {"code": "BR", "name": "Brazil", "currency": "R$", "regions": ["São Paulo", "Rio de Janeiro", "Minas Gerais", "Bahia", "Paraná", "Rio Grande do Sul", "Pernambuco", "Ceará", "Goiás", "Amazonas"]}
    ],
    "age_brackets": [
        {"value": "18-24", "label": "18-24 (Gen Z)", "traits": "High mobile usage, TikTok native, price sensitive"},
        {"value": "25-34", "label": "25-34 (Young Millennials)", "traits": "Career building, high purchasing power, Instagram active"},
        {"value": "35-44", "label": "35-44 (Older Millennials)", "traits": "Family focused, stability seeking, Facebook active"},
        {"value": "45-54", "label": "45-44 (Gen X)", "traits": "Established careers, high disposable income, LinkedIn active"},
        {"value": "55-64", "label": "55-64 (Boomers)", "traits": "Wealth preservation, health conscious, Facebook/Email heavy"},
        {"value": "65+", "label": "65+ (Seniors)", "traits": "Retirement focused, trust critical, desktop preferred"}
    ],
    "income_levels": [
        {"value": "low", "label": "Low Income", "description": "Price sensitive, deals focused, budget constrained"},
        {"value": "lower-middle", "label": "Lower Middle", "description": "Aspiring middle class, value seekers, credit users"},
        {"value": "middle", "label": "Middle Income", "description": "Comfortable, quality focused, brand conscious"},
        {"value": "upper-middle", "label": "Upper Middle", "description": "Affluent, premium seekers, experience focused"},
        {"value": "high", "label": "High Income", "description": "Luxury buyers, exclusivity focused, time poor"}
    ],
    "education_levels": [
        {"value": "secondary", "label": "Secondary School"},
        {"value": "high-school", "label": "High School / Secondary"},
        {"value": "diploma", "label": "Diploma / Certificate"},
        {"value": "bachelor", "label": "Bachelor's Degree"},
        {"value": "master", "label": "Master's Degree"},
        {"value": "doctorate", "label": "Doctorate / PhD"}
    ],
    "occupations": [
        {"value": "student", "label": "Student", "pain_points": "Budget, time, future anxiety"},
        {"value": "entry-level", "label": "Entry Level Professional", "pain_points": "Career growth, imposter syndrome, networking"},
        {"value": "mid-level", "label": "Mid Level Professional", "pain_points": "Work-life balance, career plateau, upskilling"},
        {"value": "senior-level", "label": "Senior / Executive", "pain_points": "Legacy, succession, health, wealth preservation"},
        {"value": "entrepreneur", "label": "Entrepreneur / Business Owner", "pain_points": "Cash flow, scaling, competition, burnout"},
        {"value": "freelancer", "label": "Freelancer / Gig Worker", "pain_points": "Income stability, client acquisition, benefits"},
        {"value": "homemaker", "label": "Homemaker / Caregiver", "pain_points": "Time management, financial dependence, self-care"},
        {"value": "retired", "label": "Retired", "pain_points": "Health, legacy, purpose, inflation protection"}
    ],
    "psychographics": [
        {"value": "innovators", "label": "Innovators", "traits": "Risk takers, first adopters, tech enthusiasts"},
        {"value": "early-adopters", "label": "Early Adopters", "traits": "Opinion leaders, visionaries, trend setters"},
        {"value": "early-majority", "label": "Early Majority", "traits": "Pragmatists, proven solutions, value seekers"},
        {"value": "late-majority", "label": "Late Majority", "traits": "Skeptics, price sensitive, peer pressure driven"},
        {"value": "laggards", "label": "Laggards", "traits": "Traditional, resistant to change, price focused"}
    ],
    "pain_points": [
        {"value": "financial", "label": "Financial Pressure", "description": "Debt, savings, income instability"},
        {"value": "time", "label": "Time Scarcity", "description": "Overwhelmed, busy, work-life balance"},
        {"value": "health", "label": "Health Concerns", "description": "Wellness, fitness, medical issues"},
        {"value": "career", "label": "Career Anxiety", "description": "Job security, growth, skills obsolescence"},
        {"value": "relationships", "label": "Relationship Stress", "description": "Family, social, loneliness"},
        {"value": "identity", "label": "Identity / Purpose", "description": "Self-worth, direction, meaning"},
        {"value": "security", "label": "Safety / Security", "description": "Physical safety, data privacy, stability"}
    ]
}

class AudienceData(BaseModel):
    country: str
    region: Optional[str] = None
    age_bracket: str
    gender: Optional[str] = None
    income_level: Optional[str] = None
    education: Optional[str] = None
    occupation: Optional[str] = None
    psychographic: Optional[str] = None
    primary_pain_point: Optional[str] = None
    tech_savviness: Optional[str] = "medium"  # low, medium, high
    purchase_behavior: Optional[str] = None  # impulse, research, loyal, bargain

@router.post("/analyze")
async def analyze_ad(
    ad_copy: str = Form(...),
    platform: str = Form(...),
    audience_country: str = Form(...),
    audience_age: str = Form(...),
    industry: str = Form(...),
    objective: str = Form(...),
    audience_region: Optional[str] = Form(None),
    audience_gender: Optional[str] = Form(None),
    audience_income: Optional[str] = Form(None),
    audience_education: Optional[str] = Form(None),
    audience_occupation: Optional[str] = Form(None),
    audience_psychographic: Optional[str] = Form(None),
    audience_pain_point: Optional[str] = Form(None),
    tech_savviness: Optional[str] = Form("medium"),
    purchase_behavior: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    video: Optional[UploadFile] = File(None)
):
    """
    Analyze ad with detailed audience targeting
    """
    try:
        # Build rich audience description
        audience_description = build_audience_description(
            country=audience_country,
            region=audience_region,
            age=audience_age,
            gender=audience_gender,
            income=audience_income,
            education=audience_education,
            occupation=audience_occupation,
            psychographic=audience_psychographic,
            pain_point=audience_pain_point,
            tech_savviness=tech_savviness,
            purchase_behavior=purchase_behavior
        )

        # Process media if provided
        image_analysis = ""
        video_analysis = ""

        if image:
            if not image.content_type.startswith("image/"):
                raise HTTPException(status_code=400, detail="Invalid image format")

            image_bytes = await image.read()
            if len(image_bytes) > 10 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Image too large (max 10MB)")

            analysis = media_processor.analyze_image(image_bytes)
            if "error" not in analysis:
                image_analysis = json.dumps(analysis, indent=2)

        if video:
            if not video.content_type.startswith("video/"):
                raise HTTPException(status_code=400, detail="Invalid video format")

            video_bytes = await video.read()
            if len(video_bytes) > 50 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Video too large (max 50MB)")

            analysis = media_processor.analyze_video(video_bytes)
            if "error" not in analysis:
                video_analysis = json.dumps(analysis, indent=2)

        # Prepare data for AI analysis
        analysis_data = {
            "ad_copy": ad_copy,
            "platform": platform,
            "audience": audience_description,
            "industry": industry,
            "objective": objective,
            "image_analysis": image_analysis,
            "video_analysis": video_analysis,
            "audience_data": {
                "country": audience_country,
                "region": audience_region,
                "age_bracket": audience_age,
                "demographics": {
                    "gender": audience_gender,
                    "income": audience_income,
                    "education": audience_education,
                    "occupation": audience_occupation
                },
                "psychographics": {
                    "type": audience_psychographic,
                    "pain_point": audience_pain_point,
                    "tech_savviness": tech_savviness,
                    "purchase_behavior": purchase_behavior
                }
            }
        }

        # Get AI analysis
        result = ai_engine.analyze(analysis_data)

        return {
            "success": True,
            "analysis": result,
            "audience_parsed": audience_description,
            "media_analysis": {
                "image": image_analysis if image else None,
                "video": video_analysis if video else None
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

def build_audience_description(
    country: str,
    region: Optional[str],
    age: str,
    gender: Optional[str],
    income: Optional[str],
    education: Optional[str],
    occupation: Optional[str],
    psychographic: Optional[str],
    pain_point: Optional[str],
    tech_savviness: str,
    purchase_behavior: Optional[str]
) -> str:
    """Build rich audience description from structured data"""

    parts = []

    # Location
    location = region if region else country
    parts.append(f"{age} year old")

    if gender:
        parts.append(f"{gender}")

    # Occupation and education
    if occupation:
        occ_label = get_label_from_value(AUDIENCE_CONFIG["occupations"], occupation)
        parts.append(f"{occ_label.lower()}")

    if education:
        edu_label = get_label_from_value(AUDIENCE_CONFIG["education_levels"], education)
        parts.append(f"with {edu_label}")

    # Location context
    parts.append(f"in {location}, {country}")

    # Income
    if income:
        inc_label = get_label_from_value(AUDIENCE_CONFIG["income_levels"], income)
        parts.append(f"({inc_label.lower()} bracket)")

    # Psychographic
    if psychographic:
        psych_label = get_label_from_value(AUDIENCE_CONFIG["psychographics"], psychographic)
        parts.append(f"— {psych_label}: {get_psychographic_traits(psychographic)}")

    # Pain point
    if pain_point:
        pain_desc = get_pain_point_description(pain_point)
        parts.append(f"Primary concern: {pain_desc}")

    # Tech savviness
    if tech_savviness:
        tech_desc = {
            "low": "Limited tech comfort, prefers simple interfaces",
            "medium": "Comfortable with common apps, learns new tools moderately",
            "high": "Early adopter, sophisticated digital behavior"
        }.get(tech_savviness, "")
        if tech_desc:
            parts.append(f"Digital behavior: {tech_desc}")

    # Purchase behavior
    if purchase_behavior:
        purchase_desc = {
            "impulse": "Quick decision maker, responds to urgency",
            "research": "Thorough researcher, reads reviews, compares options",
            "loyal": "Brand loyal, repeat purchaser, resistant to switching",
            "bargain": "Deal seeker, price sensitive, uses coupons/codes"
        }.get(purchase_behavior, "")
        if purchase_desc:
            parts.append(f"Purchase style: {purchase_desc}")

    return "; ".join(parts)

def get_label_from_value(options: List[dict], value: str) -> str:
    """Get label from value in options list"""
    for opt in options:
        if opt["value"] == value:
            return opt["label"]
    return value

def get_psychographic_traits(value: str) -> str:
    """Get traits for psychographic type"""
    for opt in AUDIENCE_CONFIG["psychographics"]:
        if opt["value"] == value:
            return opt["traits"]
    return ""

def get_pain_point_description(value: str) -> str:
    """Get description for pain point"""
    for opt in AUDIENCE_CONFIG["pain_points"]:
        if opt["value"] == value:
            return opt["description"]
    return value

@router.get("/audience-config")
async def get_audience_config():
    """Get all audience targeting configuration"""
    return AUDIENCE_CONFIG

@router.get("/platforms")
async def get_platforms():
    """Get supported platforms"""
    return {
        "platforms": [
            {"id": "tiktok", "name": "TikTok", "focus": "Fast hook, raw content", "best_for": ["18-24", "25-34"]},
            {"id": "facebook", "name": "Facebook", "focus": "Trust, proof, comments", "best_for": ["35-44", "45-54", "55-64"]},
            {"id": "instagram", "name": "Instagram", "focus": "Visuals, lifestyle", "best_for": ["18-24", "25-34", "35-44"]},
            {"id": "youtube", "name": "YouTube", "focus": "First 5 seconds, story", "best_for": ["18-24", "25-34", "35-44"]},
            {"id": "linkedin", "name": "LinkedIn", "focus": "Professional, B2B", "best_for": ["25-34", "35-44", "45-54"]},
            {"id": "twitter", "name": "Twitter/X", "focus": "Concise, timely", "best_for": ["25-34", "35-44"]},
            {"id": "google", "name": "Google Ads", "focus": "Intent, search match", "best_for": ["all"]}
        ]
    }

@router.get("/industries")
async def get_industries():
    """Get supported industries"""
    return {
        "industries": [
            {"id": "ecommerce", "name": "E-commerce", "risk_level": "medium"},
            {"id": "saas", "name": "SaaS", "risk_level": "low"},
            {"id": "finance", "name": "Finance / Forex / Crypto", "risk_level": "high"},
            {"id": "health", "name": "Health & Wellness", "risk_level": "medium"},
            {"id": "education", "name": "Education", "risk_level": "low"},
            {"id": "realestate", "name": "Real Estate", "risk_level": "medium"},
            {"id": "b2b", "name": "B2B Services", "risk_level": "low"},
            {"id": "apps", "name": "Consumer Apps", "risk_level": "medium"},
            {"id": "gaming", "name": "Gaming", "risk_level": "low"},
            {"id": "fashion", "name": "Fashion & Beauty", "risk_level": "medium"},
            {"id": "food", "name": "Food & Beverage", "risk_level": "low"},
            {"id": "travel", "name": "Travel & Hospitality", "risk_level": "medium"},
            {"id": "other", "name": "Other", "risk_level": "medium"}
        ]
    }
