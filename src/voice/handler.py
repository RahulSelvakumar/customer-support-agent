"""Voice input/output (STT/TTS) handling."""

import hashlib
import json
import requests
from typing import Tuple


class VoiceHandler:
    """Handles voice transcription (STT) and synthesis (TTS)."""
    
    STT_API_URL = "https://api.elevenlabs.io/v1/speech-to-text"
    TTS_API_URL = "https://api.elevenlabs.io/v1/text-to-speech"
    
    @staticmethod
    def _get_guessed_extension(mime_type: str) -> str:
        """Guess file extension from MIME type."""
        mapping = {
            "audio/webm": "webm",
            "audio/wav": "wav",
            "audio/mpeg": "mp3",
            "audio/ogg": "ogg",
            "audio/mp4": "m4a",
        }
        return mapping.get(mime_type, "webm")
    
    @staticmethod
    def transcribe_voice(
        audio_bytes: bytes,
        mime_type: str,
        api_key: str,
        cache: dict,
    ) -> Tuple[str, bool, str]:
        """Transcribe audio to text using ElevenLabs STT.
        
        Args:
            audio_bytes: Raw audio bytes
            mime_type: MIME type of audio
            api_key: ElevenLabs API key
            cache: Cache dictionary for transcripts
            
        Returns:
            (transcript, from_cache, error_message)
        """
        if not api_key:
            return "", False, "ElevenLabs API key not set."
        
        # Check cache
        audio_hash = hashlib.sha256(audio_bytes).hexdigest()
        if audio_hash in cache:
            return cache[audio_hash], True, ""
        
        try:
            guessed_ext = VoiceHandler._get_guessed_extension(mime_type)
            files = {
                "file": (f"audio.{guessed_ext}", audio_bytes, mime_type),
            }
            data = {
                "model_id": "scribe_v1",
            }
            headers = {"xi-api-key": api_key}
            
            response = requests.post(
                VoiceHandler.STT_API_URL,
                files=files,
                data=data,
                headers=headers,
                timeout=30,
            )
            
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict):
                        detail = error_data.get("detail", error_data)
                        if isinstance(detail, dict):
                            error_msg = detail.get("message", str(detail))
                        elif isinstance(detail, list):
                            error_msg = str(detail[0]) if detail else str(error_data)
                        else:
                            error_msg = str(detail)
                    else:
                        error_msg = str(error_data)
                except:
                    error_msg = response.text
                return "", False, f"ElevenLabs STT failed ({response.status_code}): {error_msg}"
            
            result = response.json()
            transcript = result.get("text", "").strip()
            
            if transcript:
                cache[audio_hash] = transcript
            
            return transcript, False, ""
        
        except requests.Timeout:
            return "", False, "ElevenLabs STT request timed out."
        except requests.RequestException as e:
            return "", False, f"ElevenLabs STT error: {str(e)}"
        except Exception as e:
            return "", False, f"Unexpected error during transcription: {str(e)}"
    
    @staticmethod
    def synthesize_voice(
        text: str,
        api_key: str,
        voice_id: str,
        model_id: str = "eleven_turbo_v2_5",
        max_chars: int = 500,
        cache: dict = None,
    ) -> Tuple[bytes, bool, str]:
        """Synthesize text to speech using ElevenLabs TTS.
        
        Args:
            text: Text to synthesize
            api_key: ElevenLabs API key
            voice_id: ElevenLabs voice ID
            model_id: Model to use
            max_chars: Character limit for free tier
            cache: Cache dictionary for audio
            
        Returns:
            (audio_bytes, from_cache, error_message)
        """
        if not api_key:
            return b"", False, "ElevenLabs API key not set."
        
        if not text or not text.strip():
            return b"", False, "No text to synthesize."
        
        # Respect character limits
        if len(text) > max_chars:
            text = text[:max_chars] + "..."
        
        # Check cache
        cache_key = f"{voice_id}|{model_id}|{text}"
        cache_hash = hashlib.sha256(cache_key.encode()).hexdigest()
        
        if cache and cache_hash in cache:
            return cache[cache_hash], True, ""
        
        try:
            url = f"{VoiceHandler.TTS_API_URL}/{voice_id}"
            headers = {
                "xi-api-key": api_key,
                "Content-Type": "application/json",
            }
            
            payload = {
                "text": text,
                "model_id": model_id,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
            }
            
            response = requests.post(
                url,
                json=payload,
                headers=headers,
                timeout=30,
            )
            
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    if isinstance(error_data, dict):
                        detail = error_data.get("detail", error_data)
                        if isinstance(detail, dict):
                            error_msg = detail.get("message", str(detail))
                        elif isinstance(detail, list):
                            error_msg = str(detail[0]) if detail else str(error_data)
                        else:
                            error_msg = str(detail)
                    else:
                        error_msg = str(error_data)
                except:
                    error_msg = response.text
                return b"", False, f"ElevenLabs TTS failed ({response.status_code}): {error_msg}"
            
            audio_bytes = response.content
            
            if cache is not None and audio_bytes:
                cache[cache_hash] = audio_bytes
            
            return audio_bytes, False, ""
        
        except requests.Timeout:
            return b"", False, "ElevenLabs TTS request timed out."
        except requests.RequestException as e:
            return b"", False, f"ElevenLabs TTS error: {str(e)}"
        except Exception as e:
            return b"", False, f"Unexpected error during synthesis: {str(e)}"
