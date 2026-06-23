"""Streamlit UI components for chat interface."""

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage
from src.utils.helpers import message_text


class ChatRenderer:
    """Renders chat messages and conversation history."""
    
    @staticmethod
    def render_chat_message(message, role: str):
        """Render a single chat message.
        
        Args:
            message: Message object (HumanMessage or AIMessage)
            role: "user" or "assistant"
        """
        avatar = "🧑" if role == "user" else "🛍️"
        with st.chat_message(role, avatar=avatar):
            st.markdown(message_text(message.content))
    
    @staticmethod
    def render_chat_history(messages: list):
        """Render all chat messages."""
        for msg in messages:
            if not msg.content or not message_text(msg.content):
                continue
            role = "user" if isinstance(msg, HumanMessage) else "assistant"
            ChatRenderer.render_chat_message(msg, role)


import streamlit as st

class InputBar:
    """Handles message input bar with mic and send buttons."""
    
    @staticmethod
    def render() -> tuple[str, bool, bool]:
        """Render input bar with text field, mic, and send buttons.
        
        Returns:
            (typed_input_text, send_clicked, mic_clicked)
        """
        # Inject precise CSS to handle both the outer layout and inner form elements
        st.html("""
            <style>
                /* Align the mic button vertically with the entire form box */
                [data-testid="stHorizontalBlock"] {
                    align-items: center !important;
                }
                
                /* Target the columns INSIDE the form specifically to flex-center them */
                form [data-testid="stHorizontalBlock"] {
                    align-items: center !important;
                }
                
                /* Remove any odd bottom margins that Streamlit applies to form buttons */
                div.stFormSubmitButton {
                    margin-bottom: 0px !important;
                    padding-top: 0px !important;
                }
                
                /* Ensure the text input wrapper doesn't push the button down */
                div[data-testid="stTextInput"] {
                    margin-bottom: 0px !important;
                }
            </style>
        """)

        # Mic button outside form
        mic_col, form_col = st.columns([1, 11])
        
        with mic_col:
            mic_clicked = st.button(
                "🎤",
                use_container_width=True,
                key="mic_toggle_btn",
                disabled=False,
                help="Record a voice message",
            )
        
        with form_col:
            with st.form(key="message_form", clear_on_submit=True):
                # Using vertical_alignment="center" alongside the CSS overrides
                input_col, send_col = st.columns([10, 1], vertical_alignment="center")
                
                with input_col:
                    typed_input = st.text_input(
                        "Message",
                        label_visibility="collapsed",
                        placeholder="Ask about refunds, returns, or your order status...",
                        key="composer_text_input",
                    )
                
                with send_col:
                    send_clicked = st.form_submit_button("➤", use_container_width=True)
        
        return typed_input, send_clicked, mic_clicked

class Telemetry:
    """Displays telemetry and agent execution logs."""
    
    @staticmethod
    def generate_html(logs: list) -> str:
        """Generate HTML for telemetry display.
        
        Args:
            logs: List of log messages
            
        Returns:
            HTML string with styled logs
        """
        log_items = "".join(
            f'<li style="margin: 4px 0; font-size: 12px; color: #666;">{log}</li>'
            for log in logs
        )
        
        return f"""
        <div style="
            background: #f9fafb; border: 1px solid #e5e7eb;
            border-radius: 6px; padding: 12px;
            max-height: 200px; overflow-y: auto;
        ">
            <p style="margin: 0 0 8px 0; font-weight: 600; font-size: 13px; color: #1f2937;">
                ⚙ Engine telemetry
            </p>
            <ul style="margin: 0; padding-left: 20px;">
                {log_items if logs else '<li style="font-size: 12px; color: #999;">No logs yet...</li>'}
            </ul>
        </div>
        """


class VoiceRecorder:
    """Handles voice recording interface."""
    
    @staticmethod
    def render(elevenlabs_key: str, live_recorder_available: bool):
        """Render voice recorder UI.
        
        Returns:
            (recorder_clip, use_recording_clicked)
        """
        if not live_recorder_available:
            st.warning(
                "Live recorder is unavailable in this running Streamlit process. "
                "Start with: `./venv/bin/streamlit run app.py`"
            )
            return None, False
        
        try:
            recorder_clip = st.audio_input(
                "Record your question",
                key="mic_audio_clip",
                help="Record and then click 'Use recording'.",
            )
        except AttributeError:
            st.warning("Audio input not available. Upgrade Streamlit.")
            return None, False
        
        use_recording = st.button(
            "Use recording",
            key="use_recording_btn",
            use_container_width=False,
            disabled=recorder_clip is None,
        )
        
        return recorder_clip, use_recording
