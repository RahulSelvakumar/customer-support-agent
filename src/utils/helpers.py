"""Utility helper functions."""

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage


def message_text(content: object) -> str:
    """Extract and clean text from message content.
    
    Handles string, list, dict, and mixed content types.
    """
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
    """Check if a message should be rendered in chat."""
    if not isinstance(message, (HumanMessage, AIMessage)):
        return False
    return bool(message_text(message.content))


def latest_assistant_text(messages: list[BaseMessage]) -> str:
    """Extract the latest assistant message text."""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage):
            text = message_text(msg.content)
            if text:
                return text
    return ""


def word_stream(text: str):
    """Generate word-by-word streaming with typing effect."""
    words = text.split()
    for i, word in enumerate(words):
        yield word + (" " if i < len(words) - 1 else "")
        import time
        time.sleep(0.05)
