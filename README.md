# Agentic AI Hub

> A comprehensive, hands-on repository for AI students and engineers to learn and build production-grade AI agents using the **OpenAI Agents SDK** with local open-source models.

```
100% Local  •  Zero Cost  •  Full Privacy  •  Production Patterns
```

---

## Repository Structure

```
agentic-ai-hub/
│
├── shared/                          #    Reusable modules (import in any agent)
│   ├── models/                      #    LLM provider configs (Ollama, LiteLLM, OpenAI, Groq)
│   │   ├── ollama_provider.py       #    Ollama local models
│   │   ├── litellm_provider.py      #    LiteLLM (100+ providers)
│   │   ├── openai_provider.py       #    OpenAI cloud models
│   │   └── groq_provider.py         #    Groq cloud (fast inference)
│   ├── tools/                       #    Reusable tool functions
│   │   ├── web_tools.py             #    Search, fetch, scrape
│   │   ├── time_tools.py            #    Date, time, timezone
│   │   ├── math_tools.py            #    Calculator, conversions
│   │   └── notification_tools.py    #    Email, Slack, SMS stubs
│   ├── schemas/                     #    Shared Pydantic models
│   │   └── common.py                #    TicketClassification, UserProfile, etc.
│   └── guardrails/                  #    Reusable guardrail functions
│       └── safety.py                #    PII detection, jailbreak, SQL injection
│
├── agents/                          #    Individual agent projects
│   ├── 01_hello_agent/              #    Simplest possible agent
│   ├── 02_support_agent/            #    Customer support with tools
│   ├── 03_devops_agent/             #    Incident response + HITL
│   ├── 04_ecommerce_multiagent/     #    Multi-agent with handoffs
│   ├── 05_banking_guarded_agent/    #    Guardrails + approval flows
│   ├── 06_voice_agent/              #    STT → LLM → TTS pipeline
│   └── 07_rag_agent/                #    RAG with knowledge base
│
├── notebooks/                       #    Learning notebooks (01-08)
│   ├── 01_agents_sdk_basics.ipynb
│   ├── 02_creating_agents.ipynb
│   ├── 03_ollama_with_agents_sdk.ipynb
│   ├── 04_tools_mastery.ipynb
│   ├── 05_guardrails.ipynb
│   ├── 06_human_in_the_loop.ipynb
│   ├── 07_handoffs.ipynb
│   └── 08_voice_agents.ipynb
│
├── .env.example                     # Environment variables template
├── pyproject.toml                   # Project metadata
└── README.md                        # This file
```

### Design Principles

| Principle | How |
|---|---|
| **Each agent is self-contained** | Every agent folder has its own `agent.py`, `tools.py`, `schemas.py`, `README.md` |
| **Shared modules are DRY** | Common tools, models, guardrails in `shared/` — import anywhere |
| **Swap models freely** | `shared/models/` has Ollama, LiteLLM, OpenAI, Groq — one-line switch |
| **Learn progressively** | Notebooks 01→08 build on each other; agents 01→07 increase complexity |
| **Production patterns** | Real industry scenarios, not toy examples |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/the-schoolofai/agentic-ai-hub.git
cd agentic-ai-hub

# 2. Setup
uv sync

# 3. Install Ollama + pull a model
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:7b

# 4. Run your first agent
cd agents/01_hello_agent
uv run agent.py

# 5. Or start with notebooks
jupyter notebook notebooks/
```

---

## Agent Index

| # | Agent | Concepts | Difficulty |
|---|---|---|---|
| 01 | **Hello Agent** | Agent, Runner, basic tools | ⭐ Beginner |
| 02 | **Support Agent** | Structured output, multi-tool, dynamic instructions | ⭐⭐ |
| 03 | **DevOps Agent** | Incident response, HITL approval, async tools | ⭐⭐⭐ |
| 04 | **E-Commerce Multi-Agent** | Handoffs, triage routing, specialist agents | ⭐⭐⭐ |
| 05 | **Banking Guarded Agent** | Input/output guardrails, PII protection, HITL | ⭐⭐⭐⭐ |
| 06 | **Voice Agent** | Faster-Whisper STT, Ollama LLM, Kokoro TTS | ⭐⭐⭐⭐ |
| 07 | **RAG Agent** | Knowledge base search, document Q&A | ⭐⭐⭐ |

---

## Tech Stack

| Component | Technology | Why |
|---|---|---|
| Agent Framework | OpenAI Agents SDK v0.13+ | Lightweight, provider-agnostic, production-ready |
| Local LLM | Ollama (Qwen 2.5, Llama 3.1) | Free, private, fast |
| Cloud LLM (optional) | OpenAI, Groq, Together | When you need more power |
| Multi-provider | LiteLLM | 100+ LLMs via single interface |
| STT | Faster-Whisper | 4x faster than Whisper, runs on CPU |
| TTS | Kokoro (82M) | Near real-time on CPU, Apache 2.0 |
| Validation | Pydantic v2 | Structured output, schema generation |

---

## Learning Path

```
1: Foundations
  Notebook 01 → SDK basics
  Notebook 02 → Creating agents properly
  Agent 01    → Hello Agent

2: Tools & Local Models
  Notebook 03 → Ollama integration
  Notebook 04 → Tools mastery
  Agent 02    → Support Agent

3: Safety & Control
  Notebook 05 → Guardrails
  Notebook 06 → Human-in-the-loop
  Agent 03    → DevOps Agent
  Agent 05    → Banking Guarded Agent

4: Multi-Agent & Voice
  Notebook 07 → Handoffs
  Notebook 08 → Voice agents
  Agent 04    → E-Commerce Multi-Agent
  Agent 06    → Voice Agent
```

---

## License

MIT — Use freely for learning and commercial projects.
