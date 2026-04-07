"""
Video Processing Service for ADLYTICS
Handles video upload, frame extraction, audio transcription, and analysis.
"""

import logging
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
import base64
import httpx

logger = logging.getLogger(__name__)

MAX_VIDEO_SIZE_BYTES = 100 * 1024 * 1024  # 100MB
SUPPORTED_FORMATS = {'mp4', 'mov', 'webm', 'mkv'}
KEY_FRAME_TIMESTAMPS = [1, 8]

# Only use a real OpenAI key for Whisper — OpenRouter keys won't work
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"

# Check if we actually have a valid OpenAI key (not OpenRouter)
HAS_WHISPER = bool(OPENAI_API_KEY and not OPENAI_API_KEY.startswith('sk-or-'))


class VideoProcessingError(Exception):
    """Custom exception for video processing errors"""
    pass


class VideoProcessor:
    """Handles video processing including frame extraction and audio transcription."""

    def __init__(self):
        self.temp_dir = None
        self.logger = logging.getLogger(__name__)

    def _validate_video_file(self, video_path: Path):
        if not video_path.exists():
            raise VideoProcessingError(f"Video file not found: {video_path}")
        file_ext = video_path.suffix.lower().lstrip('.')
        if file_ext not in SUPPORTED_FORMATS:
            raise VideoProcessingError(f"Unsupported video format: {file_ext}. Supported: {', '.join(SUPPORTED_FORMATS)}")
        file_size = video_path.stat().st_size
        if file_size > MAX_VIDEO_SIZE_BYTES:
            raise VideoProcessingError(f"Video file too large: {file_size / (1024*1024):.2f}MB. Maximum: 100MB")
        self.logger.info(f"Video validated: {video_path.name} ({file_size / (1024*1024):.2f}MB)")

    def _get_video_duration(self, video_path: Path) -> float:
        try:
            cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                   '-of', 'default=noprint_wrappers=1:nokey=1:noprint_filename=1', str(video_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            duration = float(result.stdout.strip())
            self.logger.info(f"Video duration: {duration:.2f}s")
            return duration
        except Exception as e:
            raise VideoProcessingError(f"Failed to get video duration: {str(e)}")

    def _extract_frames(self, video_path: Path, temp_dir: Path, duration: float) -> List[Dict[str, str]]:
        frames = []
        valid_timestamps = [ts for ts in KEY_FRAME_TIMESTAMPS if ts <= duration]
        if not valid_timestamps:
            valid_timestamps = [0]

        try:
            for timestamp in valid_timestamps:
                # Extract as small JPEG (512px wide, quality 5) to save memory
                frame_path = temp_dir / f"frame_{timestamp:.0f}s.jpg"
                cmd = [
                    'ffmpeg', '-i', str(video_path), '-ss', str(timestamp),
                    '-vframes', '1',
                    '-vf', 'scale=512:-1',  # Resize to 512px width
                    '-q:v', '5',  # JPEG quality (2=best, 31=worst)
                    '-y', str(frame_path)
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

                if result.returncode != 0:
                    self.logger.warning(f"Failed to extract frame at {timestamp}s")
                    continue

                with open(frame_path, 'rb') as f:
                    frame_base64 = base64.b64encode(f.read()).decode('utf-8')

                # Delete frame file immediately to free disk/memory
                frame_path.unlink(missing_ok=True)

                frames.append({'timestamp': timestamp, 'base64_image': frame_base64})
                self.logger.info(f"Extracted frame at {timestamp}s ({len(frame_base64) // 1024}KB)")

            return frames
        except Exception as e:
            raise VideoProcessingError(f"Failed to extract frames: {str(e)}")

    def _extract_audio(self, video_path: Path, temp_dir: Path) -> Optional[Path]:
        audio_path = temp_dir / "audio.mp3"
        try:
            cmd = ['ffmpeg', '-i', str(video_path), '-q:a', '0', '-map', 'a', '-y', str(audio_path)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                self.logger.warning(f"Audio extraction failed: {result.stderr[:200]}")
                return None
            self.logger.info(f"Audio extracted: {audio_path}")
            return audio_path
        except subprocess.TimeoutExpired:
            self.logger.warning("Audio extraction timed out")
            return None
        except Exception as e:
            self.logger.warning(f"Failed to extract audio: {str(e)}")
            return None

    def _transcribe_audio(self, audio_path: Path) -> str:
        """Transcribe audio using OpenAI Whisper. Returns empty string on failure."""
        if not HAS_WHISPER:
            self.logger.info("No valid OpenAI API key for Whisper — skipping transcription (frames-only analysis)")
            return ""

        try:
            audio_size = audio_path.stat().st_size
            if audio_size > 25 * 1024 * 1024:
                self.logger.warning(f"Audio too large for Whisper ({audio_size / (1024*1024):.1f}MB), skipping")
                return ""

            with open(audio_path, 'rb') as audio_file:
                files = {'file': ('audio.mp3', audio_file, 'audio/mpeg')}
                data = {'model': 'whisper-1'}
                headers = {'Authorization': f'Bearer {OPENAI_API_KEY}'}

                with httpx.Client(timeout=60.0) as client:
                    response = client.post(WHISPER_API_URL, files=files, data=data, headers=headers)
                    if response.status_code != 200:
                        self.logger.warning(f"Whisper API error ({response.status_code}): {response.text[:200]}")
                        return ""
                    result = response.json()
                    transcript = result.get('text', '')
                    self.logger.info(f"Audio transcribed: {len(transcript)} characters")
                    return transcript

        except Exception as e:
            self.logger.warning(f"Transcription failed (continuing without): {str(e)}")
            return ""

    def process_video(self, video_path: str) -> Dict:
        """Process video file: extract frames and optionally transcribe audio."""
        video_path = Path(video_path)
        self._validate_video_file(video_path)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            try:
                duration = self._get_video_duration(video_path)

                self.logger.info("Extracting frames...")
                frames = self._extract_frames(video_path, temp_path, duration)

                transcript = ""
                if HAS_WHISPER:
                    self.logger.info("Extracting audio for transcription...")
                    audio_path = self._extract_audio(video_path, temp_path)
                    if audio_path:
                        self.logger.info("Transcribing audio...")
                        transcript = self._transcribe_audio(audio_path)
                else:
                    self.logger.info("Skipping audio extraction — no Whisper key available")

                result = {
                    'frames': frames,
                    'transcript': transcript,
                    'duration_seconds': duration,
                    'frame_count': len(frames)
                }
                self.logger.info(f"Video processing complete: {len(frames)} frames, {duration:.2f}s duration")
                return result

            except VideoProcessingError:
                raise
            except Exception as e:
                self.logger.error(f"Unexpected error during video processing: {str(e)}")
                raise VideoProcessingError(f"Unexpected error: {str(e)}")


def create_video_processor() -> VideoProcessor:
    """Factory function to create a VideoProcessor instance"""
    return VideoProcessor()
