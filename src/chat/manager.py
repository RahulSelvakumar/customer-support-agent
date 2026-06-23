"""Chat history and state management."""

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage


class ChatManager:
    """Manages chat history and session state."""
    
    SESSION_STATE_KEYS = {
        "chat_history": "chat_history",
        "admin_logs": "admin_logs",
        "pending_voice_input": "pending_voice_input",
        "show_mic_recorder": "show_mic_recorder",
        "voice_transcript_cache": "voice_transcript_cache",
        "voice_cache": "voice_cache",
        "last_voice_info": "last_voice_info",
        "last_voice_transcript": "last_voice_transcript",
        "last_voice_audio": "last_voice_audio",
        "last_assistant_text": "last_assistant_text",
    }
    
    @staticmethod
    def initialize_session():
        """Initialize session state variables."""
        for key, default_key in ChatManager.SESSION_STATE_KEYS.items():
            if default_key not in st.session_state:
                if key == "chat_history":
                    st.session_state[default_key] = []
                elif key == "admin_logs":
                    st.session_state[default_key] = []
                elif key in ["voice_transcript_cache", "voice_cache"]:
                    st.session_state[default_key] = {}
                else:
                    st.session_state[default_key] = ""
    
    @staticmethod
    def add_user_message(content: str):
        """Add a user message to chat history."""
        st.session_state.chat_history.append(HumanMessage(content=content))
    
    @staticmethod
    def add_assistant_message(content: str):
        """Add an assistant message to chat history."""
        st.session_state.chat_history.append(AIMessage(content=content))
    
    @staticmethod
    def get_chat_history():
        """Get current chat history."""
        return st.session_state.chat_history
    
    @staticmethod
    def get_admin_logs():
        """Get current admin logs."""
        return st.session_state.admin_logs
    
    @staticmethod
    def update_logs(logs: list):
        """Update admin logs."""
        st.session_state.admin_logs = logs
    
    @staticmethod
    def set_pending_voice(transcript: str):
        """Set pending voice input."""
        st.session_state.pending_voice_input = transcript
    
    @staticmethod
    def get_pending_voice():
        """Get and clear pending voice input."""
        value = st.session_state.pending_voice_input
        st.session_state.pending_voice_input = ""
        return value
    
    @staticmethod
    def toggle_mic_recorder():
        """Toggle mic recorder visibility."""
        st.session_state.show_mic_recorder = not st.session_state.get("show_mic_recorder", False)
    
    @staticmethod
    def show_mic_recorder():
        """Show mic recorder."""
        st.session_state.show_mic_recorder = True
    
    @staticmethod
    def hide_mic_recorder():
        """Hide mic recorder."""
        st.session_state.show_mic_recorder = False
    
    @staticmethod
    def is_mic_recorder_visible():
        """Check if mic recorder is visible."""
        return st.session_state.get("show_mic_recorder", False)
    
    @staticmethod
    def cache_voice_transcript(key: str, value: str):
        """Cache voice transcript."""
        st.session_state.voice_transcript_cache[key] = value
    
    @staticmethod
    def get_cached_transcript(key: str):
        """Get cached transcript."""
        return st.session_state.voice_transcript_cache.get(key)
    
    @staticmethod
    def cache_voice_audio(key: str, value):
        """Cache voice audio."""
        st.session_state.voice_cache[key] = value
    
    @staticmethod
    def get_cached_audio(key: str):
        """Get cached audio."""
        return st.session_state.voice_cache.get(key)
    
    @staticmethod
    def set_voice_info(message: str):
        """Set voice status info."""
        st.session_state.last_voice_info = message
    
    @staticmethod
    def set_voice_audio(audio_bytes):
        """Set last voice audio."""
        st.session_state.last_voice_audio = audio_bytes
