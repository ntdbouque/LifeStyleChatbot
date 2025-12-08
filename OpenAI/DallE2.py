"""
DALL-E 2 Image Processing Module
Provides image description capabilities using OpenAI GPT-4 Vision API
Supports URL images and base64-encoded images with automatic format detection
"""

import os
import base64
import mimetypes
from openai import OpenAI
from icecream import ic
from typing import Dict, Any, Optional, Tuple

# Lazy initialize OpenAI client - will be created on first use
_openai_client = None


def _get_openai_client():
    """Get or create OpenAI client (lazy initialization)"""
    global _openai_client
    if _openai_client is None:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def detect_image_format(base64_str: str) -> str:
    """
    Detect image format from base64 string magic bytes
    
    Args:
        base64_str: Base64 encoded image string
        
    Returns:
        Image format (png, gif, webp, jpeg)
    """
    # Magic bytes for common image formats
    magic_bytes = {
        "iVBORw": "png",      # PNG magic: 89 50 4E 47
        "R0l": "gif",         # GIF magic: 47 49 46
        "UklGR": "webp",      # WebP magic: 52 49 46 46
        "ftyp": "heic",       # HEIC magic
        "/9j": "jpeg",        # JPEG magic: FF D8 FF
    }
    
    for magic, fmt in magic_bytes.items():
        if base64_str.startswith(magic):
            return fmt
    
    # Default to JPEG if cannot detect
    return "jpeg"


def validate_base64_image(base64_str: str) -> Tuple[bool, Optional[str]]:
    """
    Validate base64 encoded image
    
    Args:
        base64_str: Base64 string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Try to decode
        image_data = base64.b64decode(base64_str, validate=True)
        
        # Check minimum size (at least 100 bytes)
        if len(image_data) < 100:
            return False, "Image too small"
        
        # Check maximum size (10MB)
        if len(image_data) > 10 * 1024 * 1024:
            return False, "Image too large (max 10MB)"
        
        return True, None
    except Exception as e:
        return False, f"Invalid base64 format: {str(e)}"


def prepare_image_content(image_data: str) -> Dict[str, Any]:
    """
    Prepare image content for GPT-4 Vision API
    
    Args:
        image_data: URL or base64-encoded image
        
    Returns:
        Image content dict for API call
    """
    if image_data.startswith('http://') or image_data.startswith('https://'):
        # It's a URL
        return {
            "type": "image_url",
            "image_url": {"url": image_data}
        }
    else:
        # It's base64
        image_format = detect_image_format(image_data)
        return {
            "type": "image_url",
            "image_url": {"url": f"data:image/{image_format};base64,{image_data}"}
        }




def image_captioner(image_data: str, detail: str = "auto") -> str:
    """
    Describe image using OpenAI GPT-4 Vision API
    
    Args:
        image_data: Either a URL string or base64-encoded image string
        detail: Image detail level - "low", "high", or "auto" (default)
        
    Returns:
        Vietnamese description of the image focusing on medical/health content
    """
    try:
        # Validate input
        if not image_data:
            return "No image data provided"
        
        # If base64, validate it first
        if not image_data.startswith('http'):
            is_valid, error_msg = validate_base64_image(image_data)
            if not is_valid:
                return f"Invalid image: {error_msg}"
        
        client = _get_openai_client()
        
        # Prepare image content
        image_content = prepare_image_content(image_data)
        
        # Call GPT-4 Vision
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {
                    "role": "user",
                    "content": [
                        image_content,
                        {
                            "type": "text",
                            "text": "Describe this image in detail in Vietnamese. Focus on any relevant medical or health-related content. Include details about colors, text, objects, and any medical indicators if present."
                        }
                    ]
                }
            ],
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        ic(f"Error in image_captioner: {e}")
        return f"Unable to describe image: {str(e)}"


def get_image_caption(image_data: str, detail: str = "auto") -> Dict[str, Any]:
    """
    Wrapper function to get image caption with error handling
    
    Args:
        image_data: URL or base64-encoded image
        detail: Image detail level - "low", "high", or "auto"
        
    Returns:
        Dict with 'success' status and 'caption' or 'error' message
    """
    try:
        # Validate image data exists
        if not image_data:
            return {
                "success": False,
                "error": "No image data provided"
            }
        
        # Validate if base64
        if not image_data.startswith('http'):
            is_valid, error_msg = validate_base64_image(image_data)
            if not is_valid:
                return {
                    "success": False,
                    "error": error_msg
                }
        
        caption = image_captioner(image_data, detail=detail)
        return {
            "success": True,
            "caption": caption
        }
    except Exception as e:
        ic(f"Error getting image caption: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def process_multiple_images(images: list, detail: str = "auto") -> Dict[str, Any]:
    """
    Process multiple images and return captions
    
    Args:
        images: List of image URLs or base64 strings
        detail: Image detail level
        
    Returns:
        Dict with list of captions and success status
    """
    results = []
    
    for idx, image_data in enumerate(images):
        try:
            caption = image_captioner(image_data, detail=detail)
            results.append({
                "index": idx,
                "success": True,
                "caption": caption
            })
        except Exception as e:
            ic(f"Error processing image {idx}: {e}")
            results.append({
                "index": idx,
                "success": False,
                "error": str(e)
            })
    
    return {
        "success": all(r["success"] for r in results),
        "results": results
    }


if __name__ == "__main__":
    # Example usage
    test_url = "https://via.placeholder.com/100"
    result = get_image_caption(test_url)
    print(result)

