"""
Whisper-1 Speech-to-Text Module
Transcribes audio files (WAV, MP3, etc.) to text using OpenAI Whisper API
"""

import os
from openai import OpenAI
from icecream import ic
from pathlib import Path

# Lazy initialize OpenAI client
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


def transcribe_audio(audio_file_path: str, language: str = "vi") -> str:
    """
    Transcribe audio file to text using OpenAI Whisper-1 API
    
    Args:
        audio_file_path: Path to audio file (WAV, MP3, M4A, FLAC, etc.)
        language: Language code (vi for Vietnamese, en for English, etc.)
        
    Returns:
        Transcribed text from the audio file
    """
    try:
        # Validate file exists
        file_path = Path(audio_file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
        
        # Check file size (max 25MB for Whisper API)
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > 25:
            raise ValueError(f"Audio file too large: {file_size_mb:.2f}MB (max 25MB)")
        
        client = _get_openai_client()
        
        # Open and transcribe audio file
        with open(audio_file_path, 'rb') as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format="text"
            )
        
        return transcript
    
    except FileNotFoundError as e:
        ic(f"File error: {e}")
        raise
    except ValueError as e:
        ic(f"Validation error: {e}")
        raise
    except Exception as e:
        ic(f"Error transcribing audio: {e}")
        raise


def transcribe_audio_with_metadata(audio_file_path: str, language: str = "vi") -> dict:
    """
    Transcribe audio and return detailed result with metadata
    
    Args:
        audio_file_path: Path to audio file
        language: Language code
        
    Returns:
        Dict with 'success' status and 'text' or 'error' message
    """
    try:
        text = transcribe_audio(audio_file_path, language)
        return {
            "success": True,
            "text": text,
            "file": Path(audio_file_path).name,
            "language": language
        }
    except Exception as e:
        ic(f"Error in transcribe_audio_with_metadata: {e}")
        return {
            "success": False,
            "error": str(e),
            "file": Path(audio_file_path).name
        }


def transcribe_vietnamese_audio(audio_file_path: str) -> str:
    """
    Shorthand for transcribing Vietnamese audio
    
    Args:
        audio_file_path: Path to Vietnamese audio file (WAV, MP3, etc.)
        
    Returns:
        Transcribed Vietnamese text
    """
    return transcribe_audio(audio_file_path, language="vi")


def transcribe_english_audio(audio_file_path: str) -> str:
    """
    Shorthand for transcribing English audio
    
    Args:
        audio_file_path: Path to English audio file (WAV, MP3, etc.)
        
    Returns:
        Transcribed English text
    """
    return transcribe_audio(audio_file_path, language="en")


if __name__ == "__main__":
    # Example usage
    test_file = "test_audio.wav"  # Replace with actual file path
    
    if os.path.exists(test_file):
        result = transcribe_audio_with_metadata(test_file, language="vi")
        print(f"Transcription result:")
        print(f"  Success: {result['success']}")
        if result['success']:
            print(f"  Text: {result['text']}")
        else:
            print(f"  Error: {result['error']}")
    else:
        print(f"Test file '{test_file}' not found. Please provide a valid audio file path.")
