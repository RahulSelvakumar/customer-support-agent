"""
Apex Retail Support - Main Streamlit Application

A clean, modular customer support chatbot with voice integration and split-screen telemetry.
"""

import streamlit as st
from langchain_core.messages import AIMessage

# Imports from modular structure
from agent import agent_app
from src.ui.styling import apply_theme
from src.ui.components import ChatRenderer, InputBar, VoiceRecorder
from src.chat.manager import ChatManager
from src.voice.handler import VoiceHandler
from src.utils.helpers import word_stream, latest_assistant_text
from src.core.config import AppConfig, ELEVENLABS_API_KEY, DEFAULT_VOICE, DEFAULT_MODEL, MAX_VOICE_CHARS_FREE

# =============================================================================
# PAGE SETUP
# =============================================================================

st.set_page_config(
    page_title=AppConfig.__doc__ or "Apex Retail Support",
    page_icon="🛍️",
    layout="wide",
)

apply_theme()
ChatManager.initialize_session()

# Ensure the friendly initial greeting is injected immediately on load
if not ChatManager.get_chat_history():
    ChatManager.add_assistant_message("Hi! I'm Apex Retail Assistant. Share your Customer ID and Order ID, and I'll check your refund eligibility right away.")

# =============================================================================
# SIDEBAR - Settings
# =============================================================================

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    st.divider()
    st.markdown("**Voice Configuration**")
    
    voice_enabled = st.toggle(
        "Enable voice replies",
        value=st.session_state.get("voice_enabled_toggle", False),
        key="voice_enabled_toggle",
    )
    
    if voice_enabled and ELEVENLABS_API_KEY:
        voice_options = AppConfig.get_voice_ids()
        selected_voice_label = st.selectbox(
            "Voice",
            options=list(voice_options.keys()),
        )
        selected_voice_id = voice_options[selected_voice_label]
        selected_model = "eleven_turbo_v2_5"
        max_voice_chars = MAX_VOICE_CHARS_FREE
        auto_voice = st.toggle("Auto-play replies", value=False)
    else:
        selected_voice_id = AppConfig.get_default_voice()
        selected_model = DEFAULT_MODEL
        max_voice_chars = MAX_VOICE_CHARS_FREE
        auto_voice = False

# =============================================================================
# MAIN UI LAYOUT - Split Screen
# =============================================================================

col_chat, padding, col_admin = st.columns([1.5, 0.1, 1])

# --- LEFT COLUMN: Customer Chat Interface ---
with col_chat:
    # A cleaner, more minimalist header
    st.markdown("### 🛍️ Apex Retail Support")
    st.caption("Returns, refunds, and order help in one chat window.")
    
    # 1. Fixed-height container to anchor the input bar to the bottom
    chat_container = st.container(height=550)
    with chat_container:
        ChatRenderer.render_chat_history(ChatManager.get_chat_history())

    # 2. Input bar rendered directly beneath the container
    typed_input, send_clicked, mic_clicked = InputBar.render()

    # 3. Voice recording logic
    if mic_clicked:
        ChatManager.toggle_mic_recorder()

    if ChatManager.is_mic_recorder_visible():
        st.markdown("---")
        recorder_clip, use_recording = VoiceRecorder.render(
            elevenlabs_key=ELEVENLABS_API_KEY or "",
            live_recorder_available=True,
        )
        
        if use_recording and recorder_clip is not None:
            if not ELEVENLABS_API_KEY:
                st.error("Please set ELEVENLABS_API_KEY in .env file for voice transcription.")
            else:
                with st.spinner("Transcribing..."):
                    transcript, from_cache, stt_error = VoiceHandler.transcribe_voice(
                        audio_bytes=recorder_clip.getvalue(),
                        mime_type=recorder_clip.type or "audio/webm",
                        api_key=ELEVENLABS_API_KEY,
                        cache=st.session_state.get("voice_transcript_cache", {}),
                    )
                
                if stt_error:
                    st.error(stt_error)
                elif transcript:
                    ChatManager.set_pending_voice(transcript)
                    ChatManager.hide_mic_recorder()
                    st.rerun()

# --- RIGHT COLUMN: Admin Telemetry Logs ---
with col_admin:
    st.markdown("### ⚙️ Engine Telemetry")
    st.caption("Real-time reasoning logs and tool executions.")
    
    # Match the height of the chat window for UI symmetry
    log_container = st.container(height=550)
    with log_container:
        for log in ChatManager.get_admin_logs():
            if log.startswith("🤖"):
                # Visually highlight backend tool actions
                st.markdown(f"**🟢 {log}**") 
            else:
                st.caption(f"_{log}_")

# =============================================================================
# MESSAGE PROCESSING & GRAPH ROUTING
# =============================================================================

incoming_input = ""
pending_voice = ChatManager.get_pending_voice()

if pending_voice:
    incoming_input = pending_voice
elif send_clicked and typed_input.strip():
    incoming_input = typed_input.strip()

if incoming_input:
    # Add user message to state
    ChatManager.add_user_message(incoming_input)
    
    with chat_container:
        ChatRenderer.render_chat_message(
            type('Message', (), {'content': incoming_input})(),
            role="user",
        )
        
        # Streamlit loading spinner
        with st.chat_message("assistant", avatar="🛍️"):
            with st.spinner("Thinking..."):
                live_logs = ChatManager.get_admin_logs()
                response_text = ""
                
                # Execute LangGraph State Machine
                for chunk in agent_app.stream(
                    {"messages": ChatManager.get_chat_history(), "logs": live_logs}
                ):
                    for payload in chunk.values():
                        if "logs" in payload:
                            live_logs = payload["logs"]
                        if "messages" in payload:
                            candidate_text = latest_assistant_text(payload["messages"])
                            if candidate_text:
                                response_text = candidate_text
                
                # Update UI state with new backend logs
                ChatManager.update_logs(live_logs)
                
                if response_text:
                    ChatManager.add_assistant_message(response_text)
                    st.write_stream(word_stream(response_text))
                    
                    # Optional Voice Synthesis
                    if auto_voice and voice_enabled and ELEVENLABS_API_KEY:
                        audio_bytes, from_cache, voice_error = VoiceHandler.synthesize_voice(
                            text=response_text,
                            api_key=ELEVENLABS_API_KEY,
                            voice_id=selected_voice_id,
                            model_id=selected_model,
                            max_chars=max_voice_chars,
                            cache=st.session_state.get("voice_cache", {}),
                        )
                        if audio_bytes and not voice_error:
                            st.audio(audio_bytes, format="audio/mpeg", autoplay=True)
                else:
                    st.markdown("Sorry, I couldn't process that. Please try again.")
    
    st.rerun()