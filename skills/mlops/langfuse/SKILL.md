---
name: langfuse
description: "LLM observability, prompt management, and evals."
version: 0.1.0
author: Hermes
platforms: [linux, macos]
metadata:
  hermes:
    tags: [LLM, Observability, Tracing, Evaluation, Prompts]
---

# Langfuse — Open-Source LLM Engineering Platform

Langfuse is an open-source AI engineering platform for tracing, evaluating, and managing prompts across LLM applications. It supports Python and JS/TS SDKs, OpenTelemetry-based instrumentation, and a REST API. This skill covers SDK setup, tracing patterns, prompt management, and the public API — not self-hosting or infrastructure deployment.

## When to Use

- Add observability to an LLM application (OpenAI, LangChain, Vercel AI SDK, custom)
- Debug production LLM calls — trace inputs, outputs, latency, and cost
- Manage prompts with version control, labels, and templates
- Run evaluations and score LLM outputs
- Query trace data programmatically via the public API

## Prerequisites

- Python 3.8+ with `pip install langfuse` (Python SDK v4)
- Or Node.js 18+ with `npm install @langfuse/core @langfuse/client @langfuse/tracing @langfuse/otel` (JS/TS SDK v5)
- Langfuse account (cloud or self-hosted) with API credentials

### Required Environment Variables

```bash
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_BASE_URL=https://cloud.langfuse.com  # EU default
```

Data region base URLs (set `LANGFUSE_BASE_URL` to one of):
| Region | URL |
|--------|-----|
| EU | `https://cloud.langfuse.com` |
| US | `https://us.cloud.langfuse.com` |
| Japan | `https://jp.cloud.langfuse.com` |
| HIPAA | `https://hipaa.cloud.langfuse.com` |
| Self-hosted | your instance URL |

## How to Run

All examples invoke Python through the `terminal` tool or via `execute_code`. For JS/TS, use the `terminal` tool with `node`.

```python
from langfuse import get_client

langfuse = get_client()
if langfuse.auth_check():
    print("Authenticated")
```

## Quick Reference

| Action | Command / Endpoint |
|--------|-------------------|
| Install Python SDK | `pip install langfuse` |
| Install JS/TS SDK | `npm install @langfuse/core @langfuse/client @langfuse/tracing @langfuse/otel` |
| Init client | `from langfuse import get_client` → `langfuse = get_client()` |
| Auth check | `langfuse.auth_check()` |
| Create trace (REST) | `POST /api/public/traces` |
| Create observation (REST) | `POST /api/public/observations` |
| Create score (REST) | `POST /api/public/scores` |
| Create prompt (REST) | `POST /api/public/v2/prompts` |
| Fetch prompt (SDK) | `langfuse.get_prompt("name", label="production")` |
| Flush events | `langfuse.flush()` |

## Procedure

### 1. Setup and Auth

Create API credentials in the Langfuse project settings. Export them as environment variables via `terminal`:

```bash
export LANGFUSE_PUBLIC_KEY="pk-lf-..."
export LANGFUSE_SECRET_KEY="sk-lf-..."
export LANGFUSE_BASE_URL="https://cloud.langfuse.com"
```

Verify connectivity:

```python
from langfuse import get_client
langfuse = get_client()
print(langfuse.auth_check())
```

### 2. Create a Trace with Context Manager

Use `start_as_current_observation` for automatic nesting and lifecycle:

```python
from langfuse import get_client

langfuse = get_client()

with langfuse.start_as_current_observation(
    as_type="span", name="process-request", input={"query": "hello"}
) as span:
    with langfuse.start_as_current_observation(
        as_type="generation", name="llm-response", model="gpt-4o"
    ) as generation:
        generation.update(output="Generated response")
    span.update(output="Request complete")

langfuse.flush()
```

### 3. Use the `@observe` Decorator

Auto-capture inputs, outputs, timings, and errors of a function:

```python
from langfuse import observe

@observe()
def my_function(data, parameter):
    return {"result": data}

@observe(name="llm-call", as_type="generation")
async def my_llm_call(prompt_text):
    return "LLM response"
```

To disable IO capture (large payloads), set `capture_input=False` or `capture_output=False` on the decorator, or set `LANGFUSE_OBSERVE_DECORATOR_IO_CAPTURE_ENABLED=false`.

### 4. Create and Use Prompts

**Create a prompt (Python SDK):**

```python
from langfuse import get_client
langfuse = get_client()

# Text prompt with template variables
langfuse.create_prompt(
    name="movie-critic",
    type="text",
    prompt="As a {{ criticlevel }} movie critic, do you like {{ movie }}?",
    labels=["production"]
)

# Chat prompt
langfuse.create_prompt(
    name="movie-critic-chat",
    type="chat",
    prompt=[
        {"role": "system", "content": "You are an {{ criticlevel }} movie critic"},
        {"role": "user", "content": "Do you like {{ movie }}?"}
    ],
    labels=["production"]
)
```

**Fetch and render a prompt:**

```python
prompt = langfuse.get_prompt("movie-critic", label="production")
compiled = prompt.compile(criticlevel="harsh", movie="Inception")
# compiled == "As a harsh movie critic, do you like Inception?"
```

### 5. Instrument Integrations

**OpenAI (Python — drop-in SDK):**

```python
from langfuse.openai import openai  # replaces `from openai import OpenAI`

response = openai.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "1 + 1 = ?"}]
)
```

**LangChain (Python — callback handler):**

```python
from langfuse.langchain import CallbackHandler
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

langfuse_handler = CallbackHandler()
llm = ChatOpenAI(model="gpt-4o")
prompt = ChatPromptTemplate.from_template("Tell a joke about {topic}")
chain = prompt | llm

response = chain.invoke(
    {"topic": "cats"},
    config={"callbacks": [langfuse_handler]}
)
```

### 6. Public API (REST)

Authenticate with Basic Auth: username = Public Key, password = Secret Key.

```bash
curl -u pk-lf-...:sk-lf-... \
  https://cloud.langfuse.com/api/public/traces \
  -H "Content-Type: application/json"
```

Key endpoints:

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/public/traces` | Create a trace |
| GET | `/api/public/traces` | List traces |
| POST | `/api/public/observations` | Create an observation |
| POST | `/api/public/scores` | Create a score |
| POST | `/api/public/v2/prompts` | Create or update a prompt |
| GET | `/api/public/v2/prompts` | List prompts |

### 7. Evaluate and Score

Send a score (0-1) for a trace or observation:

```python
from langfuse import get_client
langfuse = get_client()

langfuse.score(
    trace_id="...",
    name="helpfulness",
    value=0.85,
    comment="Good response"
)
```

### 8. Attribute Propagation

Propagate trace-level attributes to all child observations:

```python
from langfuse import get_client, propagate_attributes

langfuse = get_client()

with langfuse.start_as_current_observation(as_type="span", name="root") as span:
    with propagate_attributes(user_id="user_123", session_id="session_abc"):
        with langfuse.start_as_current_observation(as_type="generation", name="child") as gen:
            gen.update(output="child output")
```

## Pitfalls

- **Client initialization is lazy.** The first operation triggers connection. Call `auth_check()` at startup to fail fast.
- **flush() is required in short-lived scripts.** Background workers batch and flush every ~60s, but scripts that exit immediately lose events. Always call `langfuse.flush()` at the end.
- **Nested observations auto-parent** if created inside a context manager. Manual `start_observation()` does NOT auto-close — you must call `.end()`.
- **OpenAI drop-in SDK** (`from langfuse.openai import openai`) replaces OpenAI entirely. It does NOT support the full OpenAI streaming edge cases — test streaming in staging first.
- **The `@observe` decorator can only be used on async functions** in Python (the decorator itself is synchronous but must wrap an async def). For sync functions use the context manager pattern.
- **Prompt template syntax** uses `{{ variable }}` with surrounding spaces compatible with Jinja2-style rendering.

## Verification

Run this script via the `terminal` or `execute_code` tool to confirm the SDK is installed, credentials are valid, and a trace is created:

```python
from langfuse import get_client

langfuse = get_client()
assert langfuse.auth_check(), "Auth failed — check LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY"

with langfuse.start_as_current_observation(as_type="span", name="verify-setup") as span:
    span.update(output="Langfuse skill verified")

langfuse.flush()
print("Langfuse skill verified. Trace created successfully.")
```
