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
from backend.services.benchmarks import build_benchmark_context, build_element_scoring_context, get_benchmarks, calculate_percentile

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
            section += f"\n- {len(frames)} key frames extracted (analyze the visual content in detail)"
        else:
            section += "\n- No video provided"
        if transcript:
            section += f'\n- Audio Transcript (spoken words from the video):\n"""\n{transcript}\n"""\nIMPORTANT: Analyze the voiceover/speech content — assess the hook wording, persuasion techniques, emotional tone, clarity of message, CTA strength, and how the spoken words complement the visuals.'
        else:
            section += "\n- No audio transcript available (analyze based on visuals only)"
        return section

    def _build_vision_prompt(self, ad_frames=None, ad_transcript=None, landing_frames=None, landing_transcript=None, platform="facebook", industry="finance", audience_country="nigeria", audience_age="25-34", audience_income="middle", cta_destination="telegram", brand_voice=None):
        """Build comprehensive GPT-4o Vision analysis prompt"""
        brand_voice_section = ""
        if brand_voice:
            brand_voice_section = "\n" + build_brand_voice_context(brand_voice)

        benchmark_block = build_benchmark_context(platform, industry)
        element_block = build_element_scoring_context()
        benchmarks = get_benchmarks(platform, industry)

        prompt = f"""You are ADLYTICS v8.0 — the most advanced video funnel analysis system, powered by real industry benchmark data. You are given actual frames extracted from real video ads. You MUST describe exactly what you see in the frames — the specific visuals, colors, text overlays, people, products, scenes, animations, branding elements, etc. NEVER give generic advice. Every observation and recommendation must reference specific elements visible in the frames.

CONTEXT:
- Platform: {platform}
- Industry: {industry}
- Target Country: {audience_country}
- Target Age: {audience_age}
- Target Income Level: {audience_income}
- CTA Destination: {cta_destination}

{benchmark_block}

{element_block}

AUDIENCE PERSONAS:
{json.dumps(AUDIENCE_PERSONAS, indent=2)}{brand_voice_section}

TASK 1: ANALYZE THE AD VIDEO
{self._format_video_section("AD VIDEO", ad_frames, ad_transcript)}

CRITICAL: First describe EXACTLY what you see in each frame — text, colors, people, products, logos, backgrounds, animations, overlays. Then score based on what you actually see.
Score these (0-100): hook_score, visual_quality, message_clarity, curiosity_gap, platform_fit
Provide: visual_description (detailed description of what is visible in the frames), verdict (referencing specific elements you saw), strengths (specific to this video), weaknesses (specific to this video)

TASK 2: ANALYZE THE LANDING PAGE VIDEO
{self._format_video_section("LANDING PAGE VIDEO", landing_frames, landing_transcript)}

Same approach — describe what you see first, then score.
Score these (0-100): continuity_score, depth_score, trust_building, cta_effectiveness, conversion_psychology
Provide: visual_description, verdict, strengths, weaknesses

TASK 3: ANALYZE THE COMPLETE FUNNEL WITH DROP-OFF ANALYSIS
The funnel has three stages: Hook (first 3 seconds) → Message (middle section) → CTA (end)
Score: message_escalation (0-100), drop_off_risk (Low/Medium/High), audience_funnel_fit (0-100), predicted_conversion (level + range), overall_score (0-100)
Provide: funnel_summary (2-3 sentences summarizing the overall funnel flow referencing specific visual elements from both videos)

For drop_off_analysis, predict viewer retention at each stage:
- stage_1_retention: % viewers retained through Hook (first 3 seconds)
- stage_2_retention: % viewers retained through Message (middle)
- stage_3_retention: % viewers retained through CTA (end)
- primary_drop_point: Which stage has the biggest drop (Hook→Message or Message→CTA)
- drop_reason: Specific reason referencing actual content seen in the frames
- recovery_tactic: Specific change referencing actual content that needs to change

TASK 4: Provide 3-5 prioritized recommendations. Each MUST reference specific elements from the video frames (e.g. "The red text overlay at timestamp X is hard to read" or "The product shot lacks close-up detail"). Include: priority (P1/P2/P3), area, issue (specific to this video), fix (actionable and specific), expected_impact

TASK 5: Provide improved versions of both scripts that address the specific issues found

TASK 6: PLATFORM-SPECIFIC PREDICTIONS
Based on the funnel analysis, predict performance on each platform referencing specific visual elements:
- facebook: Score 0-100 and reasoning referencing specific video elements
- tiktok: Score 0-100 and reasoning
- instagram: Score 0-100 and reasoning
- youtube: Score 0-100 and reasoning

Return valid JSON:
{{
  "ad_video_analysis": {{"hook_score": 0, "visual_quality": 0, "message_clarity": 0, "curiosity_gap": 0, "platform_fit": 0, "visual_description": "Detailed description of what is visible in the ad video frames - colors, text, people, products, scenes, branding", "audio_analysis": "Analysis of voiceover/speech content if transcript was provided - tone, persuasion, clarity. Empty string if no audio.", "verdict": "Assessment referencing specific visual AND audio elements", "strengths": ["Specific strength referencing actual content"], "weaknesses": ["Specific weakness referencing actual content"]}},
  "landing_video_analysis": {{"continuity_score": 0, "depth_score": 0, "trust_building": 0, "cta_effectiveness": 0, "conversion_psychology": 0, "visual_description": "Detailed description of landing video frames", "audio_analysis": "Analysis of voiceover/speech if available", "verdict": "Assessment referencing specific visual AND audio elements", "strengths": [], "weaknesses": []}},
  "funnel_analysis": {{
    "message_escalation": 0,
    "drop_off_risk": "",
    "drop_off_point": "",
    "audience_funnel_fit": 0,
    "funnel_summary": "2-3 sentence summary of the funnel flow referencing specific visuals from both videos",
    "predicted_conversion": {{"level": "", "range": ""}},
    "overall_score": 0,
    "drop_off_analysis": {{
      "stage_1_retention": 0,
      "stage_2_retention": 0,
      "stage_3_retention": 0,
      "primary_drop_point": "",
      "drop_reason": "Specific reason referencing actual video content",
      "recovery_tactic": "Specific tactic referencing what needs to change"
    }},
    "platform_predictions": {{
      "facebook": {{"score": 0, "reason": ""}},
      "tiktok": {{"score": 0, "reason": ""}},
      "instagram": {{"score": 0, "reason": ""}},
      "youtube": {{"score": 0, "reason": ""}}
    }}
  }},
  "element_breakdown": [
    {{"element": "headline", "score": 0, "observation": "what you see in the text overlay or first spoken words", "impact": "high|medium|low", "fix": "specific improvement"}},
    {{"element": "color_palette", "score": 0, "observation": "dominant colors, contrast, brand consistency", "impact": "medium", "fix": ""}},
    {{"element": "logo_placement", "score": 0, "observation": "where and when logo appears", "impact": "low", "fix": ""}},
    {{"element": "music_audio", "score": 0, "observation": "background music energy, trending sounds", "impact": "medium", "fix": ""}},
    {{"element": "voiceover", "score": 0, "observation": "narration tone, pacing, persuasion", "impact": "high", "fix": ""}},
    {{"element": "video_pacing", "score": 0, "observation": "cut frequency, transitions, energy", "impact": "medium", "fix": ""}},
    {{"element": "cta_design", "score": 0, "observation": "CTA text, button, placement", "impact": "high", "fix": ""}},
    {{"element": "text_overlays", "score": 0, "observation": "on-screen text readability", "impact": "medium", "fix": ""}},
    {{"element": "social_proof", "score": 0, "observation": "testimonials, numbers, trust badges", "impact": "high", "fix": ""}}
  ],
  "predictive_performance": {{
    "predicted_ctr": "X.X%-X.X%",
    "predicted_cpa": "$XX-$XX",
    "predicted_cvr": "X.X%-X.X%",
    "percentile_rank": 0,
    "benchmark_comparison": "above_average|average|below_average",
    "confidence_level": "high|medium|low",
    "key_driver": "The single element most responsible for predicted performance",
    "vs_industry_avg": "Outperforms X% of {industry} ads on {platform}"
  }},
  "recommendations": [{{"priority": "P1", "area": "", "issue": "Specific issue referencing actual video content", "fix": "Specific actionable fix", "expected_impact": "Estimated impact with reasoning"}}],
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
                        "max_tokens": 6000
                    }
                )

                if response.status_code != 200:
                    error_detail = response.text[:500]
                    self.logger.error(f"OpenRouter API error: {response.status_code} - {error_detail}")
                    raise HTTPException(status_code=500, detail=f"AI analysis failed (HTTP {response.status_code}): {error_detail}")

                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                finish_reason = result.get("choices", [{}])[0].get("finish_reason", "unknown")
                self.logger.info(f"OpenRouter response received: {len(content)} chars, finish_reason={finish_reason}")

                try:
                    if not content or not content.strip():
                        self.logger.error("OpenRouter returned empty content")
                        raise ValueError("AI returned empty response — model may have timed out")

                    # Strip markdown code blocks if present
                    import re
                    code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
                    if code_block_match:
                        content = code_block_match.group(1)

                    json_start = content.find("{")
                    json_end = content.rfind("}") + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = content[json_start:json_end]
                        analysis = json.loads(json_str)
                    else:
                        self.logger.error(f"No JSON braces found in response. First 500 chars: {content[:500]}")
                        raise ValueError("No JSON found in response — AI may have returned plain text")
                except json.JSONDecodeError as e:
                    self.logger.error(f"Failed to parse AI response as JSON: {str(e)}\nFirst 500 chars: {content[:500]}")
                    raise HTTPException(status_code=500, detail=f"Failed to parse AI analysis response: {str(e)}")

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


async def transcribe_audio_via_openrouter(audio_base64: str, label: str = "video") -> str:
    """Transcribe audio using OpenRouter's audio-capable model.
    Sends base64 WAV audio to GPT-4o-audio-preview for transcription.
    Falls back gracefully if transcription fails."""
    if not OPENROUTER_API_KEY or not audio_base64:
        return ""

    try:
        logger.info(f"Transcribing {label} audio via OpenRouter ({len(audio_base64) // 1024}KB base64)")
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "openai/gpt-4o-audio-preview",
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Transcribe this audio exactly. Return ONLY the spoken words, nothing else. If there is no speech, return 'NO_SPEECH'."},
                            {
                                "type": "input_audio",
                                "input_audio": {
                                    "data": audio_base64,
                                    "format": "wav"
                                }
                            }
                        ]
                    }],
                    "temperature": 0.0,
                    "max_tokens": 1000
                }
            )

            if response.status_code != 200:
                logger.warning(f"Audio transcription failed ({response.status_code}): {response.text[:200]}")
                return ""

            result = response.json()
            transcript = result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

            if transcript and transcript != "NO_SPEECH":
                logger.info(f"Transcribed {label} audio: {len(transcript)} chars")
                return transcript
            else:
                logger.info(f"No speech detected in {label} audio")
                return ""

    except Exception as e:
        logger.warning(f"Audio transcription error for {label}: {str(e)}")
        return ""


@router.post("/analyze-frames")
async def analyze_video_funnel_frames(
    ad_frames_json: str = Form(..., description="JSON array of base64 JPEG frames from ad video"),
    landing_frames_json: Optional[str] = Form(None, description="JSON array of base64 JPEG frames from landing video"),
    ad_audio_base64: Optional[str] = Form(None, description="Base64 WAV audio extracted from ad video"),
    landing_audio_base64: Optional[str] = Form(None, description="Base64 WAV audio extracted from landing video"),
    platform: str = Form("facebook"),
    industry: str = Form("finance"),
    audience_country: str = Form("nigeria"),
    audience_age: str = Form("25-34"),
    audience_income: str = Form("middle"),
    cta_destination: str = Form("telegram"),
    brand_voice: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """Analyze video funnel using pre-extracted frames and optional audio (extracted in browser)."""
    logger.info(f"Starting frames-based funnel analysis - Platform: {platform}, Industry: {industry}")

    analyzer = VideoFunnelAnalyzer()
    parsed_brand_voice = None

    try:
        # Parse frames JSON
        ad_frames = json.loads(ad_frames_json)
        if not ad_frames:
            raise HTTPException(status_code=400, detail="At least one ad video frame is required")

        # Convert to the format expected by analyze_with_vision
        ad_frame_data = [{"base64_image": f} for f in ad_frames[:2]]

        landing_frame_data = None
        if landing_frames_json:
            landing_frames = json.loads(landing_frames_json)
            if landing_frames:
                landing_frame_data = [{"base64_image": f} for f in landing_frames[:2]]

        # Transcribe audio if provided (runs in parallel)
        ad_transcript = ""
        landing_transcript = ""
        if ad_audio_base64:
            ad_transcript = await transcribe_audio_via_openrouter(ad_audio_base64, "ad")
        if landing_audio_base64:
            landing_transcript = await transcribe_audio_via_openrouter(landing_audio_base64, "landing")

        if ad_transcript:
            logger.info(f"Ad transcript: {ad_transcript[:100]}...")
        if landing_transcript:
            logger.info(f"Landing transcript: {landing_transcript[:100]}...")

        if brand_voice:
            try:
                parsed_brand_voice = json.loads(brand_voice)
            except json.JSONDecodeError:
                parsed_brand_voice = None

        has_audio = bool(ad_transcript or landing_transcript)
        logger.info(f"Analyzing {len(ad_frame_data)} ad frames, {len(landing_frame_data) if landing_frame_data else 0} landing frames, audio: {has_audio}")
        analysis = await analyzer.analyze_with_vision(
            ad_frames=ad_frame_data, ad_transcript=ad_transcript or None,
            landing_frames=landing_frame_data, landing_transcript=landing_transcript or None,
            platform=platform, industry=industry, audience_country=audience_country,
            audience_age=audience_age, audience_income=audience_income, cta_destination=cta_destination,
            brand_voice=parsed_brand_voice
        )

        logger.info("Frames-based funnel analysis completed successfully")
        return {
            "success": True,
            "analysis": analysis,
            "metadata": {
                "platform": platform, "industry": industry,
                "audience": {"country": audience_country, "age_range": audience_age, "income_level": audience_income},
                "cta_destination": cta_destination,
                "analysis_type": "frames-with-audio" if has_audio else "frames-only",
                "has_transcript": has_audio
            }
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid frames JSON format")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in frames-based analysis: {str(e)}")
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
