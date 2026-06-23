# Apex Retail Support - AI Customer Support Agent

A **production-ready, enterprise-grade** AI Customer Support Agent with voice capabilities that evaluates and processes e-commerce refund requests. This project demonstrates professional software architecture, strict policy enforcement, real-time reasoning observability, and two-way voice integration.

## ✨ Highlights

- **Enterprise Architecture:** Modular, testable, reusable codebase (see [ARCHITECTURE.md](ARCHITECTURE.md))
- **Voice Integration:** Two-way voice with ElevenLabs (speech-to-text & text-to-speech)
- **Deterministic Policy:** Refund validation that LLM cannot override
- **Real-time Telemetry:** Live agent reasoning & execution logs
- **Professional Code:** 6 focused modules, clean separation of concerns

## 🛠 Technical Stack

- **LLM:** Google Gemini 2.5 Flash (fast, accurate, cost-effective)
- **Orchestration:** LangGraph for deterministic state machine routing
- **Frontend:** Streamlit with ChatGPT-style UI & voice support
- **Voice:** ElevenLabs TTS (text-to-speech) & STT (speech-to-text)
- **Backend:** Python with clean modular architecture
- **CRM:** Mock JSON database with 15 customer profiles
- **Policy:** Markdown-based refund policy with strict validation

## 🏗 System Architecture

The application uses **layered architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────┐
│          Streamlit UI (app_refactored.py)       │
│  Chat interface, voice I/O, telemetry display   │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────┐
│             UI & Chat Modules                   │
│  ┌─────────────┐  ┌──────────────┐              │
│  │ ui/         │  │ chat/        │              │
│  │ styling.py  │  │ manager.py   │              │
│  │ components. │  │              │              │
│  │ py          │  └──────────────┘              │
│  └─────────────┘                                │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────┐
│         Business Logic & Integrations           │
│  ┌─────────────┐  ┌──────────────┐              │
│  │ voice/      │  │ core/        │              │
│  │ handler.py  │  │ config.py    │              │
│  └─────────────┘  └──────────────┘              │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────┐
│         Utilities & Helpers                     │
│  ┌──────────────────────────────────────────┐   │
│  │ utils/helpers.py                         │   │
│  └──────────────────────────────────────────┘   │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────┴──────────────────────────────┐
│       External Systems & Agents                 │
│  ┌──────────────────────────────────────────┐   │
│  │ agent.py (LangGraph)                     │   │
│  │ tools.py (CRM, Policy, Refunds)          │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### Data Flow

```
User Input
    ↓
Streamlit UI (app.py)
    ↓
ChatManager (session state)
    ↓
InputBar.render() (text/voice)
    ↓
VoiceHandler (optional STT)
    ↓
agent_app.stream() [LangGraph]
    ↓
tools.py (CRM lookup, policy check, refund execution)
    ↓
ChatManager (save response)
    ↓
ChatRenderer (display message)
    ↓
VoiceHandler (optional TTS)
    ↓
User Output (text + audio)
```
## Agent Logic Execution Flow

The agent transitions through a predictable lifecycle to process any incoming customer input:

1.  **Extract Intent:** The agent determines if the user is asking about a refund, order status, or general inquiry.
2.  **Context Loading (CRM):** If a refund is requested, the agent invokes `fetch_customer_profile()` to pull order history, account status, and dates from the mock CRM.
3.  **Policy Guarding:** The agent executes `validate_against_policy()`, cross-referencing the order date against strict policy timelines (e.g., the 14-day window constraint).
4.  **Deterministic Evaluation:** The orchestration engine verifies the output fields from the policy tool. If conditions fail, the state graph routes directly to a polite denial, ensuring the LLM cannot override the constraint through conversational manipulation ("holding the line").
5.  **Execution or Escalation:** Eligible requests trigger `execute_refund()`. High-friction scenarios or edge cases invoke `escalate_to_human()`.

## 📁 Project Structure (Refactored)

```
customer-support-agent/
├── src/                          # Core application modules
│   ├── __init__.py
│   ├── core/                     # Configuration
│   │   ├── __init__.py
│   │   └── config.py            # API keys, constants, defaults
│   ├── ui/                       # User interface
│   │   ├── __init__.py
│   │   ├── styling.py           # CSS themes, HTML templates
│   │   └── components.py        # Reusable UI widgets
│   ├── chat/                     # Chat management
│   │   ├── __init__.py
│   │   └── manager.py           # Session state, message history
│   ├── voice/                    # Voice I/O
│   │   ├── __init__.py
│   │   └── handler.py           # ElevenLabs TTS/STT
│   └── utils/                    # Utilities
│       ├── __init__.py
│       └── helpers.py           # Text extraction, streaming
│
├── app.py                        # Main Streamlit app (DEPRECATED)
├── app_refactored.py             # Main Streamlit app (RECOMMENDED)
├── agent.py                      # LangGraph orchestration
├── tools.py                      # Agent tools (CRM, policy)
├── config.py                     # Legacy config (DEPRECATED)
├── test.py                       # Test script
│
├── data/                         # Data files
│   ├── crm_mock.json            # Customer profiles
│   └── refund_policy.md         # Refund policy rules
│
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables
├── .env.example                  # Example env file
│
├── README.md                     # This file
├── ARCHITECTURE.md               # Detailed architecture docs
├── REFACTORING_SUMMARY.md        # Refactoring overview
├── REFACTORING_README.md         # Refactored structure guide
│
└── venv/                         # Python virtual environment
```

### Module Purposes

| Module | Purpose | Key Classes |
|--------|---------|------------|
| `src/core/config.py` | Configuration management | `AppConfig` |
| `src/ui/styling.py` | UI theming | CSS constants |
| `src/ui/components.py` | UI widgets | `ChatRenderer`, `InputBar`, `Telemetry`, `VoiceRecorder` |
| `src/chat/manager.py` | Session state | `ChatManager` |
| `src/voice/handler.py` | Voice I/O | `VoiceHandler` |
| `src/utils/helpers.py` | Utilities | Helper functions |
| `agent.py` | Agent logic | LangGraph state machine |
| `tools.py` | Agent tools | CRM, policy, refund functions |

## Optional Voice Mode (ElevenLabs)

The Streamlit app includes two-way voice using ElevenLabs:
- **Voice input:** record speech in the sidebar and send it through ElevenLabs Speech-to-Text.
- **Voice output:** convert assistant replies into spoken audio (manual or auto mode).

1. Set `ELEVENLABS_API_KEY` in your `.env` file.
2. Open **Voice replies (ElevenLabs)** in the right panel and enable voice mode.
3. Use **Send voice message** to transcribe and submit your recorded speech.
4. Use **Generate voice for latest reply** (or auto-voice) to hear the assistant.

Token-saving controls included in the UI:
- Voice mode is disabled by default.
- Speech-to-text only runs when you click **Send voice message**.
- Spoken text is capped by a character limit slider.
- Generated audio is cached by reply text to avoid duplicate API calls.
- Transcripts are cached by audio hash to avoid repeated STT calls.
