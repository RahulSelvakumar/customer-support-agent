"""UI styling and theme configuration."""

CSS_STYLES = """
<style>
/* ============================================
   FORCE LIGHT THEME - Fix text visibility
   ============================================ */

/* Force light background everywhere */
.stApp, .main, [data-testid="stAppViewContainer"] {
    background-color: #ffffff !important;
}

/* Force dark text on ALL elements */
.stApp *, 
.main *,
[data-testid="stAppViewContainer"] * {
    color: #1a1a1a !important;
}

/* Sidebar - light gray background, dark text */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div {
    background-color: #f5f5f5 !important;
}

[data-testid="stSidebar"] * {
    color: #1a1a1a !important;
}

/* Header - white text on blue */
.chat-header {
    background: #2563eb !important;
    padding: 20px !important;
    border-radius: 10px !important;
    margin-bottom: 20px !important;
    text-align: center !important;
}

.chat-header h2,
.chat-header p {
    color: #ffffff !important;
}

.chat-header h2 {
    font-size: 20px !important;
    font-weight: 600 !important;
    margin: 0 !important;
}

.chat-header p {
    font-size: 14px !important;
    margin: 8px 0 0 0 !important;
    opacity: 0.9 !important;
}

/* Input field - white bg, dark text */
input, textarea {
    background-color: #ffffff !important;
    color: #1a1a1a !important;
    border: 1px solid #d1d5db !important;
}

input::placeholder, textarea::placeholder {
    color: #6b7280 !important;
}

/* Buttons - white text on blue */
.stButton > button {
    background-color: #2563eb !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    height: 42px !important;
    margin-top: 25px !important;
}

.stButton > button:hover {
    background-color: #1d4ed8 !important;
    color: #ffffff !important;
}

/* Form buttons */
[data-testid="stFormSubmitButton"] > button {
    background-color: #2563eb !important;
    color: #ffffff !important;
    margin-top: 25px !important;
}

/* Chat messages - ensure dark text */
[data-testid="stChatMessage"],
[data-testid="stChatMessageContent"] {
    background-color: #f9fafb !important;
}

[data-testid="stChatMessage"] *,
[data-testid="stChatMessageContent"] * {
    color: #1a1a1a !important;
}

/* Markdown content */
.stMarkdown, .stMarkdown * {
    color: #1a1a1a !important;
}

/* Labels and captions */
label, .stCaption, small, span {
    color: #374151 !important;
}

/* Links stay blue */
a {
    color: #2563eb !important;
}

/* Dividers */
hr, [data-testid="stDecoration"] {
    background-color: #e5e7eb !important;
    border-color: #e5e7eb !important;
}

/* Expanders */
.streamlit-expanderHeader {
    color: #1a1a1a !important;
    background-color: #f9fafb !important;
}

/* Selectbox and other inputs */
[data-testid="stSelectbox"] *,
[data-testid="stSlider"] *,
[data-testid="stCheckbox"] *,
.stSelectbox *,
.stSlider *,
.stCheckbox * {
    color: #1a1a1a !important;
}

/* Toggle switch label */
[data-testid="stWidgetLabel"] {
    color: #1a1a1a !important;
}

/* Error/warning/info boxes */
.stAlert * {
    color: #1a1a1a !important;
}

/* Spinner text */
.stSpinner * {
    color: #1a1a1a !important;
}

/* ============================================
   AUDIO INPUT - Fix visibility
   ============================================ */

/* Audio recorder container - light background */
[data-testid="stAudioInput"] {
    background-color: #f3f4f6 !important;
    border-radius: 8px !important;
    padding: 8px !important;
}

[data-testid="stAudioInput"] > div,
[data-testid="stAudioInput"] > div > div,
[data-testid="stAudioInput"] > div > div > div {
    background-color: #f3f4f6 !important;
    background: #f3f4f6 !important;
}

/* Audio recorder icons and buttons - make them visible */
[data-testid="stAudioInput"] button,
[data-testid="stAudioInput"] svg {
    color: #2563eb !important;
    fill: #2563eb !important;
}

/* All text inside audio input including timestamp */
[data-testid="stAudioInput"] * {
    color: #1a1a1a !important;
    background-color: transparent !important;
}

/* The waveform/progress bar area */
[data-testid="stAudioInput"] [class*="wave"],
[data-testid="stAudioInput"] [class*="audio"],
[data-testid="stAudioInput"] [class*="Audio"] {
    background-color: #e5e7eb !important;
}

/* Timestamp text specifically */
[data-testid="stAudioInput"] span,
[data-testid="stAudioInput"] time,
[data-testid="stAudioInput"] [class*="time"],
[data-testid="stAudioInput"] [class*="duration"] {
    color: #f2f2f2 !important;
}

/* Force the inner dark container to be light */
[data-testid="stAudioInput"] [data-testid] {
    background-color: #f3f4f6 !important;
    background: #f3f4f6 !important;
}
</style>
"""

SUPPORT_SHELL_HTML = """
<div class="chat-header">
    <h2>🛍️ Apex Support</h2>
    <p>How can we help you today?</p>
</div>
"""

AUTO_SCROLL_JS = ""


def apply_theme():
    """Apply custom CSS theme to Streamlit app."""
    import streamlit as st
    st.markdown(CSS_STYLES, unsafe_allow_html=True)


def render_support_header():
    """Render the support header."""
    import streamlit as st
    st.markdown(SUPPORT_SHELL_HTML, unsafe_allow_html=True)
