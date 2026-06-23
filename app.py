import streamlit as st
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from agent import agent_app
import hashlib
import json
import os
import requests
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

st.set_page_config(page_title="Apex Retail Support", page_icon="🛍️", layout="wide")

# Custom CSS for better UI styling
st.markdown(
    """
    <style>
    /* Input field styling */
    input[type="text"] {
        background-color: #f3f4f6 !important;
        color: #1f2937 !important;
        border: 1px solid #d1d5db !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        font-size: 14px !important;
    }
    input[type="text"]::placeholder {
        color: #9ca3af !important;
    }
    input[type="text"]:focus {
        outline: none !important;
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1) !important;
    }
    
    /* Button styling - general */
    .stButton {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    
    .stButton > button {
        border-radius: 6px !important;
        font-weight: 500 !important;
        border: none !important;
        padding: 8px 10px !important;
        height: 40px !important;
        width: 100% !important;
        font-size: 16px !important;
        cursor: pointer !important;
        transition: all 0.2s ease !important;
    }
    
    /* Specifically target the mic button column */
    [data-testid="column"] .stButton > button:nth-of-type(1) {
        background-color: #3b82f6 !important;
        color: white !important;
    }
    [data-testid="column"] .stButton > button:nth-of-type(1):hover {
        background-color: #2563eb !important;
    }
    
    /* Form send button - Green */
    form .stButton > button {
        background-color: #10b981 !important;
        color: white !important;
    }
    form .stButton > button:hover {
        background-color: #059669 !important;
    }
    
    /* Remove form padding */
    .stForm {
        border: none !important;
        padding: 0 !important;
        gap: 0 !important;
    }
    
    /* Column alignment */
    [data-testid="column"] {
        gap: 0.5rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def message_text(content: object) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                cleaned = item.strip()
                if cleaned:
                    parts.append(cleaned)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text.strip())
        return "\n\n".join(parts).strip()
    return str(content).strip()


def should_render_message(message: BaseMessage) -> bool:
    if not isinstance(message, (HumanMessage, AIMessage)):
        return False
    return bool(message_text(message.content))


def latest_assistant_text(messages: list[BaseMessage]) -> str:
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            text = message_text(msg.content)
            if text:
                return text
    return ""


def word_stream(text: str):
    words = text.split()
    for i, word in enumerate(words):
        suffix = " " if i < len(words) - 1 else ""
        yield f"{word}{suffix}"
        time.sleep(0.02)


def telemetry_html(logs: list[str]) -> str:
    html = "<div class='telemetry-shell'><div class='telemetry-title'>⚙ Engine telemetry</div>"
    for log in logs:
        color = "#34d399" if log.startswith("🤖") else "#94a3b8"
        html += f"<div style='color:{color}; margin-bottom:6px;'>• {log}</div>"
    html += "</div>"
    return html


def synthesize_voice(
    text: str,
    api_key: str,
    voice_id: str,
    model_id: str,
    max_chars: int,
    cache: dict[str, bytes],
) -> tuple[bytes | None, bool, str | None]:
    trimmed_text = text.strip()[:max_chars]
    if not trimmed_text:
        return None, False, "No assistant response available for voice output."

    cache_key = hashlib.sha256(
        f"{voice_id}|{model_id}|{trimmed_text}".encode("utf-8")
    ).hexdigest()
    if cache_key in cache:
        return cache[cache_key], True, None

    payload = {
        "text": trimmed_text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.45,
            "similarity_boost": 0.8,
            "style": 0.0,
            "use_speaker_boost": True,
        },
    }
    request = Request(
        url=f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=30) as response:
            audio_bytes = response.read()
    except HTTPError as error:
        details = error.read().decode("utf-8", errors="ignore")
        return None, False, f"ElevenLabs request failed ({error.code}): {details}"
    except URLError as error:
        return None, False, f"Unable to reach ElevenLabs: {error.reason}"
    except TimeoutError:
        return None, False, "ElevenLabs timed out while generating audio."

    cache[cache_key] = audio_bytes
    return audio_bytes, False, None


def transcribe_voice(
    audio_bytes: bytes,
    mime_type: str,
    api_key: str,
    cache: dict[str, str],
) -> tuple[str | None, bool, str | None]:
    if not audio_bytes:
        return None, False, "No audio captured for transcription."

    cache_key = hashlib.sha256(audio_bytes).hexdigest()
    if cache_key in cache:
        return cache[cache_key], True, None

    try:
        guessed_extension = "webm"
        if "wav" in mime_type:
            guessed_extension = "wav"
        elif "mpeg" in mime_type or "mp3" in mime_type:
            guessed_extension = "mp3"
        elif "ogg" in mime_type:
            guessed_extension = "ogg"
        elif "mp4" in mime_type or "m4a" in mime_type:
            guessed_extension = "m4a"

        response = requests.post(
            "https://api.elevenlabs.io/v1/speech-to-text",
            headers={"xi-api-key": api_key, "Accept": "application/json"},
            data={"model_id": "scribe_v1"},
            files={
                "file": (
                    f"voice_input.{guessed_extension}",
                    audio_bytes,
                    mime_type or "audio/webm",
                )
            },
            timeout=40,
        )
    except requests.RequestException as error:
        return None, False, f"Unable to reach ElevenLabs STT: {error}"

    if not response.ok:
        return None, False, f"ElevenLabs STT failed ({response.status_code}): {response.text}"

    payload = response.json()
    transcript = (payload.get("text") or "").strip()
    if not transcript:
        return None, False, "Speech was detected but no text transcript was returned."

    cache[cache_key] = transcript
    return transcript, False, None


st.markdown(
    """
    <style>
        #MainMenu, footer, header {visibility: hidden;}
        .stApp {
            background: linear-gradient(180deg, #f7f8fc 0%, #eff2f9 100%);
            font-family: "Inter", sans-serif;
            color: #111827;
        }
        .support-shell {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 16px;
            padding: 18px 20px;
            box-shadow: 0 10px 26px rgba(17, 24, 39, 0.08);
            margin-bottom: 14px;
        }
        .support-title {
            font-size: 1.2rem;
            font-weight: 700;
            margin: 0;
            color: #0f172a;
        }
        .support-subtitle {
            margin: 4px 0 0 0;
            color: #64748b;
            font-size: 0.92rem;
        }
        .stChatMessage {
            border-radius: 14px;
            border: 1px solid #e5e7eb;
            background: #ffffff;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.05);
            padding: 0.6rem 0.85rem;
        }
        .stChatMessage p, .stChatMessage li, .stChatMessage span {
            color: #111827 !important;
        }
        [data-testid="stChatMessageContent"] {
            color: #111827 !important;
        }
        [data-testid="stChatMessage"]:has([aria-label="chat message user"]) {
            background: #eef4ff !important;
            border-color: #c7dcff !important;
        }
        [data-testid="stChatMessage"]:has([aria-label="chat message assistant"]) {
            background: #ffffff !important;
        }
        .telemetry-shell {
            background: #0f172a;
            color: #cbd5e1;
            border-radius: 14px;
            border: 1px solid #1e293b;
            padding: 14px 16px;
            max-height: 70vh;
            overflow-y: auto;
            font-family: "JetBrains Mono", monospace;
            font-size: 0.82rem;
        }
        .telemetry-title {
            font-size: 0.9rem;
            color: #e2e8f0;
            margin-bottom: 10px;
            font-weight: 600;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        AIMessage(
            content=(
                "Hi! I’m Apex Retail Assistant. Share your Customer ID and Order ID, and "
                "I’ll check refund eligibility right away."
            )
        )
    ]
if "admin_logs" not in st.session_state:
    st.session_state.admin_logs = ["System initialized. Routing engine connected."]
if "voice_cache" not in st.session_state:
    st.session_state.voice_cache = {}
if "last_assistant_text" not in st.session_state:
    st.session_state.last_assistant_text = ""
if "last_voice_audio" not in st.session_state:
    st.session_state.last_voice_audio = None
if "last_voice_info" not in st.session_state:
    st.session_state.last_voice_info = ""
if "voice_transcript_cache" not in st.session_state:
    st.session_state.voice_transcript_cache = {}
if "pending_voice_input" not in st.session_state:
    st.session_state.pending_voice_input = ""
if "last_voice_transcript" not in st.session_state:
    st.session_state.last_voice_transcript = ""
if "composer_text" not in st.session_state:
    st.session_state.composer_text = ""
if "show_mic_recorder" not in st.session_state:
    st.session_state.show_mic_recorder = False
if "voice_mode_enabled" not in st.session_state:
    st.session_state.voice_mode_enabled = False
if "voice_chars_limit" not in st.session_state:
    st.session_state.voice_chars_limit = 280
if "voice_choice" not in st.session_state:
    st.session_state.voice_choice = "Rachel (default)"

col_chat, col_admin = st.columns([2.2, 1], gap="large")

with col_admin:
    st.markdown(
        """
        <div class="support-shell">
            <p class="support-title">Customer confidence</p>
            <p class="support-subtitle">Secure payments • Fast refunds • 24×7 support</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    elevenlabs_key = os.getenv("ELEVENLABS_API_KEY") or os.getenv("ELEVENLABS_CLIENT_KEY")
    with st.expander("🔊 Voice replies (ElevenLabs)", expanded=False):
        if not elevenlabs_key:
            st.warning("Set ELEVENLABS_API_KEY to enable voice replies.")
        voice_enabled = st.toggle(
            "Enable voice mode",
            key="voice_mode_enabled",
            disabled=not bool(elevenlabs_key),
            help="Disabled by default to reduce free-tier usage.",
        )
        auto_voice = voice_enabled
        if voice_enabled:
            st.caption("Voice mode active: each assistant reply will return text + audio.")
        max_voice_chars = st.slider(
            "Spoken characters per reply (token saver)",
            min_value=120,
            max_value=700,
            key="voice_chars_limit",
            step=20,
            disabled=not voice_enabled,
        )
        voice_options = {
            "Rachel (default)": "21m00Tcm4TlvDq8ikWAM",
            "Bella": "EXAVITQu4vr4xnSDxMaL",
            "Antoni": "ErXwobaYiN019PkySvjV",
        }
        selected_voice_label = st.selectbox(
            "Voice",
            options=list(voice_options.keys()),
            key="voice_choice",
            disabled=not voice_enabled,
        )
        selected_voice_id = voice_options[selected_voice_label]
        selected_model = "eleven_multilingual_v2"
        live_recorder_available = hasattr(st, "audio_input")
        if not live_recorder_available:
            st.error(
                "Live mic recorder needs Streamlit >= 1.39.0. "
                "Please run: `pip install -U streamlit`"
            )

        if st.session_state.last_voice_transcript:
            st.caption(f"Last transcript: {st.session_state.last_voice_transcript}")

        generate_clicked = st.button(
            "Generate voice for latest reply",
            disabled=not voice_enabled or not st.session_state.last_assistant_text,
            use_container_width=True,
        )
        if generate_clicked:
            audio_bytes, from_cache, error = synthesize_voice(
                text=st.session_state.last_assistant_text,
                api_key=elevenlabs_key or "",
                voice_id=selected_voice_id,
                model_id=selected_model,
                max_chars=max_voice_chars,
                cache=st.session_state.voice_cache,
            )
            if error:
                st.session_state.last_voice_info = error
                st.session_state.last_voice_audio = None
            elif audio_bytes:
                st.session_state.last_voice_audio = audio_bytes
                source = "cache" if from_cache else "ElevenLabs API"
                st.session_state.last_voice_info = f"Voice reply ready ({source})."

        if st.session_state.last_voice_info:
            st.caption(st.session_state.last_voice_info)
        if st.session_state.last_voice_audio:
            st.audio(st.session_state.last_voice_audio, format="audio/mpeg")

    telemetry_placeholder = st.empty()
    telemetry_placeholder.markdown(
        telemetry_html(st.session_state.admin_logs), unsafe_allow_html=True
    )

with col_chat:
    st.markdown(
        """
        <div class="support-shell">
            <p class="support-title">🛍️ Apex Retail Support</p>
            <p class="support-subtitle">Returns, refunds, and order help in one chat window.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            if not should_render_message(msg):
                continue
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            avatar = "🧑" if role == "user" else "🛍️"
            with st.chat_message(role, avatar=avatar):
                st.markdown(message_text(msg.content))

    # Input bar with input | mic | send layout
    with st.form(key="message_form", clear_on_submit=True):
        input_col, mic_col, send_col = st.columns([10, 1, 1])
        
        with input_col:
            typed_input = st.text_input(
                "Message",
                label_visibility="collapsed",
                placeholder="Ask about refunds, returns, or your order status...",
                key="composer_text_input",
            )
        
        with mic_col:
            mic_clicked = st.button(
                "🎤",
                use_container_width=True,
                key="mic_toggle_btn",
                disabled=False,
                help="Record a voice message",
            )
        
        with send_col:
            send_clicked = st.form_submit_button("➤", use_container_width=True)
    
    if mic_clicked:
        if not elevenlabs_key:
            st.session_state.last_voice_info = "Set ELEVENLABS_API_KEY to use the mic recorder."
            st.session_state.show_mic_recorder = False
        else:
            st.session_state.show_mic_recorder = not st.session_state.show_mic_recorder
    
    incoming_input = ""
    if send_clicked and typed_input.strip():
        incoming_input = typed_input.strip()

    if st.session_state.show_mic_recorder and bool(elevenlabs_key):
        if not live_recorder_available:
            st.warning(
                "Live recorder is unavailable in this running Streamlit process. "
                "Start with: `./venv/bin/streamlit run app.py`"
            )
        else:
            recorder_clip = st.audio_input(
                "Record your question",
                key="mic_audio_clip",
                help="Record and then click 'Use recording'.",
            )
            use_recording = st.button(
                "Use recording",
                key="use_recording_btn",
                use_container_width=False,
                disabled=recorder_clip is None,
            )
            selected_clip = recorder_clip or st.session_state.get("mic_audio_clip")
            if use_recording and selected_clip is not None:
                with st.spinner("Transcribing voice message..."):
                    transcript, from_cache, stt_error = transcribe_voice(
                        audio_bytes=selected_clip.getvalue(),
                        mime_type=selected_clip.type or "audio/webm",
                        api_key=elevenlabs_key or "",
                        cache=st.session_state.voice_transcript_cache,
                    )
                if stt_error:
                    st.session_state.last_voice_info = stt_error
                    st.error(stt_error)
                elif transcript:
                    st.session_state.last_voice_transcript = transcript
                    source = "cache" if from_cache else "ElevenLabs STT"
                    st.session_state.last_voice_info = f"Voice captured via {source}."
                    st.session_state.pending_voice_input = transcript
                    st.session_state.show_mic_recorder = False
                    st.rerun()

    if not incoming_input and st.session_state.pending_voice_input:
        incoming_input = st.session_state.pending_voice_input
        st.session_state.pending_voice_input = ""

    if incoming_input:
        user_input = incoming_input
        st.session_state.chat_history.append(HumanMessage(content=user_input))
        with chat_container:
            with st.chat_message("user", avatar="🧑"):
                st.markdown(user_input)

            with st.chat_message("assistant", avatar="🛍️"):
                status = st.empty()
                status.caption("Apex assistant is typing...")
                live_logs = st.session_state.admin_logs
                response_text = ""
                for chunk in agent_app.stream(
                    {"messages": st.session_state.chat_history, "logs": st.session_state.admin_logs}
                ):
                    for payload in chunk.values():
                        if "logs" in payload:
                            live_logs = payload["logs"]
                            telemetry_placeholder.markdown(
                                telemetry_html(live_logs), unsafe_allow_html=True
                            )
                        if "messages" in payload:
                            candidate_text = latest_assistant_text(payload["messages"])
                            if candidate_text:
                                response_text = candidate_text

                st.session_state.admin_logs = live_logs
                if response_text:
                    st.session_state.chat_history.append(AIMessage(content=response_text))
                    st.session_state.last_assistant_text = response_text

                if response_text:
                    st.write_stream(word_stream(response_text))
                    if auto_voice and voice_enabled and elevenlabs_key:
                        voice_audio, from_cache, voice_error = synthesize_voice(
                            text=response_text,
                            api_key=elevenlabs_key,
                            voice_id=selected_voice_id,
                            model_id=selected_model,
                            max_chars=max_voice_chars,
                            cache=st.session_state.voice_cache,
                        )
                        if voice_error:
                            st.session_state.last_voice_info = voice_error
                            st.session_state.last_voice_audio = None
                        elif voice_audio:
                            st.session_state.last_voice_audio = voice_audio
                            source = "cache" if from_cache else "ElevenLabs API"
                            st.session_state.last_voice_info = f"Voice reply ready ({source})."
                            st.audio(voice_audio, format="audio/mpeg")
                else:
                    st.markdown("I couldn't generate a response. Please try again.")
                status.empty()
        
        # Form with clear_on_submit=True handles the clearing automatically, just rerun
        st.rerun()