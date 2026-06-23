"""Configuration and constants."""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")

# Voice Settings
VOICE_IDS = {
    "Rachel": "21m00Tcm4TlvDq8ikWAM",
    "Clyde": "2EiwWnXFnvU5JabPnXlBw",
    "Bella": "EXAVITQu4vr4xnSDxMaL",
    "Antoni": "ErXwobaYiN019PkySvjV",
}

DEFAULT_VOICE = "Rachel"
DEFAULT_MODEL = "eleven_turbo_v2_5"
MAX_VOICE_CHARS_FREE = 500

# Chat Config
APP_TITLE = "Apex Retail Support"
APP_ICON = "🛍️"
SIDEBAR_TITLE = "🔊 Voice replies (ElevenLabs)"

# Streamlit Config
LAYOUT = "wide"
PAGE_ICON = "🛍️"

# Feature Flags
AUTO_VOICE_ENABLED_DEFAULT = False


def get_llm():
    """Get configured LLM instance (Google Gemini).
    
    Returns:
        ChatGoogleGenerativeAI: Configured Gemini LLM
    """
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=GEMINI_API_KEY,
        temperature=0.7,
    )


class AppConfig:
    """Application configuration."""
    
    @staticmethod
    def get_voice_ids() -> dict:
        """Get available voice options."""
        return VOICE_IDS
    
    @staticmethod
    def get_default_voice() -> str:
        """Get default voice ID."""
        return VOICE_IDS.get(DEFAULT_VOICE, list(VOICE_IDS.values())[0])
    
    @staticmethod
    def has_api_keys() -> tuple[bool, bool]:
        """Check if required API keys are set.
        
        Returns:
            (has_gemini, has_elevenlabs)
        """
        return (
            bool(GEMINI_API_KEY),
            bool(ELEVENLABS_API_KEY),
        )
    
    @staticmethod
    def validate_config() -> list[str]:
        """Validate configuration and return list of missing keys.
        
        Returns:
            List of missing environment variables
        """
        missing = []
        if not GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        if not ELEVENLABS_API_KEY:
            missing.append("ELEVENLABS_API_KEY")
        return missing
