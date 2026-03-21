"""
ADLYTICS Media Processor v4.1
Handles image and video file processing
"""

from fastapi import UploadFile
import io
from PIL import Image
import os

# Max file sizes
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB

async def process_media(file: UploadFile, media_type: str = "image") -> dict:
    """
    Process uploaded media file (image or video)

    Args:
        file: FastAPI UploadFile object
        media_type: "image" or "video"

    Returns:
        dict with processed file info
    """
    if not file:
        return None

    # Read file content
    content = await file.read()

    # Check file size
    file_size = len(content)
    max_size = MAX_IMAGE_SIZE if media_type == "image" else MAX_VIDEO_SIZE

    if file_size > max_size:
        raise ValueError(f"{media_type} file too large. Max size: {max_size / 1024 / 1024}MB")

    # Process based on type
    if media_type == "image":
        return await process_image(content, file.filename)
    elif media_type == "video":
        return await process_video(content, file.filename)
    else:
        raise ValueError(f"Unsupported media type: {media_type}")


async def process_image(content: bytes, filename: str) -> dict:
    """Process image file - resize if needed, return metadata"""
    try:
        # Open image
        img = Image.open(io.BytesIO(content))

        # Get image info
        width, height = img.size
        format_type = img.format or "unknown"

        # Convert to RGB if necessary (for JPEG)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')

        # Resize if too large (max 1920x1080)
        max_width, max_height = 1920, 1080
        if width > max_width or height > max_height:
            ratio = min(max_width / width, max_height / height)
            new_size = (int(width * ratio), int(height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            width, height = new_size

        # Save to bytes
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85)
        processed_content = output.getvalue()

        return {
            "type": "image",
            "filename": filename,
            "original_size": len(content),
            "processed_size": len(processed_content),
            "width": width,
            "height": height,
            "format": "JPEG",
            "content": processed_content
        }

    except Exception as e:
        # Return original if processing fails
        return {
            "type": "image",
            "filename": filename,
            "original_size": len(content),
            "processed_size": len(content),
            "format": "original",
            "content": content,
            "error": str(e)
        }


async def process_video(content: bytes, filename: str) -> dict:
    """Process video file - return metadata without heavy processing"""
    # For videos, we just validate and return metadata
    # Heavy video processing would require ffmpeg

    # Basic validation - check if it's a video file by extension
    video_extensions = ['.mp4', '.mov', '.avi', '.webm', '.mkv']
    ext = os.path.splitext(filename.lower())[1]

    if ext not in video_extensions:
        raise ValueError(f"Unsupported video format: {ext}. Supported: {video_extensions}")

    return {
        "type": "video",
        "filename": filename,
        "size": len(content),
        "format": ext.replace('.', ''),
        "content": content,
        "note": "Video processing limited to metadata extraction"
    }


# Backward compatibility alias
process_uploaded_file = process_media
