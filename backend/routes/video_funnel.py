"""
Video Funnel Analyzer Route
ADLYTICS - AI-powered video funnel analysis for multi-stage advertising funnels

Analyzes two-video advertising funnels (ad platform video + landing page video)
and predicts performance based on engagement, messaging clarity, and funnel fit.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any
import base64
import json

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import httpx

from backend.services.video_processor import create_video_processor, VideoProcessingError
from backend.services.ai_engine import build_brand_voice_context

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/video-funnel",
    tags=["video-funnel"],
    responses={400: {"description": "Bad request"}, 500: {"description": "Internal server error"}}
)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
VISION_MODEL = "openai/gpt-4o"
TEXT_MODEL = "openai/gpt-4o"
REQUEST_TIMEOUT = 180.0

AUDIENCE_PERSONAS = {
    "lagos_scroller": {
        "name": "Lagos Scroller",
        "platform_behavior": "Quick scrolls, stops for cultural relevance",
        "decision_speed": "Fast (1-3 seconds)",
        "trust_drivers": "Social proof, local success stories",
        "pain_points": "Time-poor, skeptical of ads"
    },
    "abuja_professional": {
        "name": "Abuja Professional",
        "platform_behavior": "Scrolls deliberately, seeks credibility",
        "decision_speed": "Medium (5-10 seconds)",
        "trust_drivers": "Authority, credentials, case studies",
        "pain_points": "Busy, needs clear ROI"
    },
    "uk_compliance_officer": {
        "name": "UK Compliance Officer",
        "platform_behavior": "Skeptical, reads fine print",
        "decision_speed": "Slow (10+ seconds)",
        "trust_drivers": "Legal clarity, regulatory compliance",
        "pain_points": "Risk-averse, needs guarantees"
    },
    "us_buyer": {
        "name": "US Buyer",
        "platform_behavior": "Engagement-driven, action-oriented",
        "decision_speed": "Fast (2-5 seconds)",
        "trust_drivers": "Testimonials, money-back guarantees",
        "pain_points": "Overwhelmed with options"
    },
    "general_audience": {
        "name": "General Audience",
        "platform_behavior": "Variable, context-dependent",
        "decision_speed": "Medium (5 seconds)",
        "trust_drivers": "Clarity, relatability, value proposition",
        "pain_points": "Skepticism, banner blindness"
    }
}


class VideoFunnelAnalyzer:
    """Handles video funnel analysis using GPT-4o Vision via OpenRouter API"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.video_processor = create_video_processor()

    async def process_video_file(self, file: UploadFile) -> Dict[str, Any]:
        """Process uploaded video file to extract frames and transcript."""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
                content = await file.read()
                tmp.write(content)
                tmp.flush()
                result = self.video_processor.process_video(tmp.name)
                Path(tmp.name).unlink()
                return result
        except VideoProcessingError as e:
            self.logger.error(f"Video processing error: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error processing video: {str(e)}")
            raise VideoProcessingError(f"Failed to process video: {str(e)}")

    def _format_video_section(self, label, frames=None, transcript=None):
        """Format video data for the prompt"""
        section = f"\n{label}:"
        if frames:
            section += f"\n- {len(frames)} key frames extracted"
        else:
            section += "\n- No video provided"
        if transcript:
            section += f'\n- Transcript:\n"""\n{transcript}\n"""'
        else:
            section += "\n- No transcript available"
        return section

    def _build_vision_prompt(self, ad_frames=None, ad_transcript=None, landing_frames=None, landing_transcript=None, platform="facebook", industry="finance", audience_country="nigeria", audience_age="25-34", audience_income="middle", cta_destination="telegram", brand_voice=None):
        """Build comprehensive GPT-4o Vision analysis prompt"""
        brand_voice_section = ""
        if brand_voice:
            brand_voice_section = "\n" + build_brand_voice_context(brand_voice)

        prompt = f"""You are an expert video funnel analyst for digital advertising. Analyze this two-stage advertising funnel.

CONTEXT:
- Platform: {platform}
- Industry: {industry}
- Target Country: {audience_country}
- Target Age: {audience_age}
- Target Income Level: {audience_income}
- CTA Destination: {cta_destination}

AUDIENCE PERSONAS:
{json.dumps(AUDIENCE_PERSONAS, indent=2)}{brand_voice_section}

TASK 1: ANALYZE THE AD VIDEO
{self._format_video_section("AD VIDEO", ad_frames, ad_transcript)}

Score these (0-100): hook_score, visual_quality, message_clarity, curiosity_gap, platform_fit

TASK 2: ANALYZE THE LANDING PAGE VIDEO
{self._format_video_section("LANDING PAGE VIDEO", landing_frames, landing_transcript)}

Score these (0-100): continuity_score, depth_score, trust_building, cta_effectiveness, conversion_psychology

TASK 3: ANALYZE THE COMPLETE FUNNEL WITH DROP-OFF ANALYSIS
The funnel has three stages: Hook (first 3 seconds) → Message (middle section) → CTA (end)
Score: message_escalation (0-100), drop_off_risk (Low/Medium/High), audience_funnel_fit (0-100), predicted_conversion (level + range), overall_score (0-100)

For drop_off_analysis, predict viewer retention at each stage:
- stage_1_retention: % viewers retained through Hook (first 3 seconds)
- stage_2_retention: % viewers retained through Message (middle)
- stage_3_retention: % viewers retained through CTA (end)
- primary_drop_point: Which stage has the biggest drop (Hook→Message or Message→CTA)
- drop_reason: Why do viewers drop at that point
- recovery_tactic: Specific change to recover those viewers

TASK 4: Provide 3-5 prioritized recommendations with priority, area, issue, fix, expected_impact

TASK 5: Provide improved versions of both scripts

TASK 6: PLATFORM-SPECIFIC PREDICTIONS
Based on the funnel analysis, predict how this funnel would perform on each platform with:
- facebook: Score 0-100 and reasoning
- tiktok: Score 0-100 and reasoning
- instagram: Score 0-100 and reasoning
- youtube: Score 0-100 and reasoning

Return valid JSON:
{{
  "ad_video_analysis": {{"hook_score": 0, "visual_quality": 0, "message_clarity": 0, "curiosity_gap": 0, "platform_fit": 0, "verdict": "", "strengths": [], "weaknesses": []}},
  "landing_video_analysis": {{"continuity_score": 0, "depth_score": 0, "trust_building": 0, "cta_effectiveness": 0, "conversion_psychology": 0, "verdict": "", "strengths": [], "weaknesses": []}},
  "funnel_analysis": {{
    "message_escalation": 0,
    "drop_off_risk": "",
    "drop_off_point": "",
    "audience_funnel_fit": 0,
    "predicted_conversion": {{"level": "", "range": ""}},
    "overall_score": 0,
    "drop_off_analysis": {{
      "stage_1_retention": 0,
      "stage_2_retention": 0,
      "stage_3_retention": 0,
      "primary_drop_point": "",
      "drop_reason": "",
      "recovery_tactic": ""
    }},
    "platform_predictions": {{
      "facebook": {{"score": 0, "reason": ""}},
      "tiktok": {{"score": 0, "reason": ""}},
      "instagram": {{"score": 0, "reason": ""}},
      "youtube": {{"score": 0, "reason": ""}}
    }}
  }},
  "recommendations": [{{"priority": "", "area": "", "issue": "", "fix": "", "expected_impact": ""}}],
  "improved_scripts": {{"ad_video_script": "", "landing_video_script": "", "why_these_work": ""}}
}}"""
        return prompt

    async def analyze_with_vision(self, ad_frames=None, ad_transcript=None, landing_frames=None, landing_transcript=None, platform="facebook", industry="finance", audience_country="nigeria", audience_age="25-34", audience_income="middle", cta_destination="telegram", brand_voice=None):
        """Analyze video funnel using GPT-4o Vision via OpenRouter API."""
        if not OPENROUTER_API_KEY:
            raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not configured")

        prompt = self._build_vision_prompt(
            ad_frames=ad_frames, ad_transcript=ad_transcript,
            landing_frames=landing_frames, landing_transcript=landing_transcript,
            platform=platform, industry=industry, audience_country=audience_country,
            audience_age=audience_age, audience_income=audience_income, cta_destination=cta_destination,
            brand_voice=brand_voice
        )

        message_content = [{"type": "text", "text": prompt}]

        # Limit to 2 frames per video to stay within memory/token limits
        if ad_frames:
            for frame in ad_frames[:2]:
                if "base64_image" in frame:
                    message_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{frame['base64_image']}"}
                    })

        if landing_frames:
            for frame in landing_frames[:2]:
                if "base64_image" in frame:
                    message_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{frame['base64_image']}"}
                    })

        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.post(
                    f"{OPENROUTER_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": VISION_MODEL,
                        "messages": [{"role": "user", "content": message_content}],
                        "temperature": 0.7,
                        "max_tokens": 4000
                    }
                )

                if response.status_code != 200:
                    error_detail = response.text
                    self.logger.error(f"OpenRouter API error: {response.status_code} - {error_detail}")
                    raise HTTPException(status_code=500, detail=f"AI analysis failed: {error_detail}")

                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")

                try:
                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = content[json_start:json_end]
                        analysis = json.loads(json_str)
                    else:
                        raise ValueError("No JSON found in response")
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse AI response as JSON: {str(e)}")
                    raise HTTPException(status_code=500, detail="Failed to parse AI analysis response")

                return analysis

        except httpx.RequestError as e:
            self.logger.error(f"OpenRouter API request error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to connect to AI service: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error during analysis: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze")
async def analyze_video_funnel(
    ad_video: Optional[UploadFile] = File(None),
    landing_video: Optional[UploadFile] = File(None),
    ad_video_script: Optional[str] = Form(None),
    landing_video_script: Optional[str] = Form(None),
    platform: str = Form("facebook"),
    industry: str = Form("finance"),
    audience_country: str = Form("nigeria"),
    audience_age: str = Form("25-34"),
    audience_income: str = Form("middle"),
    cta_destination: str = Form("telegram"),
    brand_voice: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """Analyze a video advertising funnel (ad platform video + landing page video)."""
    logger.info(f"Starting video funnel analysis - Platform: {platform}, Industry: {industry}")

    if not ad_video and not ad_video_script:
        raise HTTPException(status_code=400, detail="Either ad_video file or ad_video_script text is required")

    analyzer = VideoFunnelAnalyzer()
    ad_frames = None
    ad_transcript = None
    landing_frames = None
    landing_transcript = None
    parsed_brand_voice = None

    try:
        # Parse brand_voice JSON if provided
        if brand_voice:
            try:
                parsed_brand_voice = json.loads(brand_voice)
            except json.JSONDecodeError:
                logger.warning("Invalid brand_voice JSON provided, proceeding without brand voice")
                parsed_brand_voice = None

        if ad_video:
            logger.info(f"Processing ad video: {ad_video.filename}")
            ad_result = await analyzer.process_video_file(ad_video)
            ad_frames = ad_result.get("frames")
            ad_transcript = ad_result.get("transcript")
        elif ad_video_script:
            ad_transcript = ad_video_script

        if landing_video:
            logger.info(f"Processing landing video: {landing_video.filename}")
            landing_result = await analyzer.process_video_file(landing_video)
            landing_frames = landing_result.get("frames")
            landing_transcript = landing_result.get("transcript")
        elif landing_video_script:
            landing_transcript = landing_video_script

        logger.info("Running AI analysis with GPT-4o Vision")
        analysis = await analyzer.analyze_with_vision(
            ad_frames=ad_frames, ad_transcript=ad_transcript,
            landing_frames=landing_frames, landing_transcript=landing_transcript,
            platform=platform, industry=industry, audience_country=audience_country,
            audience_age=audience_age, audience_income=audience_income, cta_destination=cta_destination,
            brand_voice=parsed_brand_voice
        )

        logger.info("Video funnel analysis completed successfully")
        return {
            "success": True,
            "analysis": analysis,
            "metadata": {
                "platform": platform, "industry": industry,
                "audience": {"country": audience_country, "age_range": audience_age, "income_level": audience_income},
                "cta_destination": cta_destination
            }
        }

    except HTTPException:
        raise
    except VideoProcessingError as e:
        logger.error(f"Video processing error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Video processing failed: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in video funnel analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/analyze-script")
async def analyze_video_funnel_script(
    ad_script: str = Form(...),
    landing_script: Optional[str] = Form(None),
    platform: str = Form("facebook"),
    industry: str = Form("finance"),
    audience_country: str = Form("nigeria"),
    audience_age: str = Form("25-34"),
    audience_income: str = Form("middle"),
    cta_destination: str = Form("telegram"),
    brand_voice: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """Analyze a video advertising funnel using text scripts only (no video upload)."""
    logger.info(f"Starting script-based funnel analysis - Platform: {platform}, Industry: {industry}")

    if not ad_script or not ad_script.strip():
        raise HTTPException(status_code=400, detail="ad_script is required and cannot be empty")

    analyzer = VideoFunnelAnalyzer()
    parsed_brand_voice = None

    try:
        # Parse brand_voice JSON if provided
        if brand_voice:
            try:
                parsed_brand_voice = json.loads(brand_voice)
            except json.JSONDecodeError:
                logger.warning("Invalid brand_voice JSON provided, proceeding without brand voice")
                parsed_brand_voice = None

        logger.info("Running AI analysis with text scripts")
        analysis = await analyzer.analyze_with_vision(
            ad_frames=None, ad_transcript=ad_script,
            landing_frames=None, landing_transcript=landing_script,
            platform=platform, industry=industry, audience_country=audience_country,
            audience_age=audience_age, audience_income=audience_income, cta_destination=cta_destination,
            brand_voice=parsed_brand_voice
        )

        logger.info("Script-based funnel analysis completed successfully")
        return {
            "success": True,
            "analysis": analysis,
            "metadata": {
                "platform": platform, "industry": industry,
                "audience": {"country": audience_country, "age_range": audience_age, "income_level": audience_income},
                "cta_destination": cta_destination,
                "analysis_type": "script-only"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in script-based analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
