import json
import os
from typing import AsyncGenerator, Dict, List, Optional
import httpx

# Supported / Validated Groq Models
ALLOWED_MODELS = {
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
    "deepseek-r1-distill-llama-70b",
}

DEFAULT_MODEL = "openai/gpt-oss-120b"

VENTUREMIND_BASE_PROMPT = """You are VentureMind AI — an elite Autonomous Startup Co-Founder, Venture Architect, and Product Intelligence Advisor.

Your mission is to empower founders with rigorous, actionable, and data-driven guidance on:
- Startup Validation & Problem-Solution Fit
- Customer Discovery & Persona Profiling
- Market Positioning & Competitive Moat Strategy
- Pricing Architecture & SaaS Unit Economics
- Financial Runway, CAC/LTV & Burn Optimization
- Go-to-Market (GTM) Acceleration & Growth Loops
- Pitch Deck Strategy, Narrative Structure & Investor Readiness
- Technical Architecture & Product Execution Decisions

Operational Principles:
1. Analytical & Direct: Provide concise, high-signal, practical advice. Avoid fluff and corporate buzzwords.
2. Constructive Skepticism: Actively challenge weak assumptions, identify blind spots, and stress-test risky hypotheses.
3. Fact vs. Assumption Clarity: Distinguish verified data points from hypotheses requiring founder testing.
4. Actionable Next Steps: Conclude with clear, prioritized tactical experiments or milestones.
5. Honesty on Live Data: Do not invent or hallucinate live market data; state clearly when an assumption is based on general industry benchmarks.

Formatting:
- Structure your response with clean Markdown (headings, bullet points, bold key terms)."""


class AIError(Exception):
    """Base exception for AI service errors."""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AIConfigError(AIError):
    """Raised when AI API key or required configuration is missing."""
    def __init__(self, message: str = "Groq API key is not configured."):
        super().__init__(message, status_code=503)


class AIAuthError(AIError):
    """Raised when authentication with Groq fails."""
    def __init__(self, message: str = "Groq authentication failed. Invalid API key."):
        super().__init__(message, status_code=401)


class AIRateLimitError(AIError):
    """Raised when Groq rate limits are reached."""
    def __init__(self, message: str = "Groq rate limit exceeded. Please try again in a few moments."):
        super().__init__(message, status_code=429)


class AIConnectionError(AIError):
    """Raised when connection to Groq fails or times out."""
    def __init__(self, message: str = "Connection to Groq service failed or timed out."):
        super().__init__(message, status_code=504)


class AIAPIError(AIError):
    """Raised when Groq returns a generic 4xx/5xx API error."""
    def __init__(self, message: str, status_code: int = 502):
        super().__init__(message, status_code=status_code)


def get_groq_api_key() -> str:
    """Retrieve Groq API key from environment."""
    key = os.getenv("GROQ_API_KEY", "").strip()
    return key


def get_default_model() -> str:
    """Retrieve default Groq model from environment or fallback."""
    return os.getenv("GROQ_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL


def sanitize_model(requested_model: Optional[str]) -> str:
    """Validate requested model against allowed Groq models list."""
    if not requested_model:
        return get_default_model()

    clean_model = requested_model.strip().lower()

    # Normalize common aliases
    if "gpt-oss" in clean_model or "120b" in clean_model:
        return "openai/gpt-oss-120b"
    if "llama-3.3" in clean_model or "70b-versatile" in clean_model:
        return "llama-3.3-70b-versatile"
    if "llama-3.1" in clean_model or "8b-instant" in clean_model:
        return "llama-3.1-8b-instant"
    if "mixtral" in clean_model:
        return "mixtral-8x7b-32768"
    if "deepseek" in clean_model:
        return "deepseek-r1-distill-llama-70b"

    if clean_model in ALLOWED_MODELS:
        return clean_model

    return get_default_model()


def build_system_prompt(startup=None) -> str:
    """Construct full VentureMind system prompt with dynamic startup context if available."""
    prompt = VENTUREMIND_BASE_PROMPT
    if startup:
        prompt += "\n\n--- ACTIVE STARTUP PROJECT CONTEXT ---"
        prompt += f"\nProject Name: {startup.name}"
        if getattr(startup, "description", None):
            prompt += f"\nConcept / Value Proposition: {startup.description}"
        if getattr(startup, "created_at", None):
            prompt += f"\nProject Registered Date: {startup.created_at.strftime('%Y-%m-%d')}"
        prompt += "\nIncorporate this startup's specific domain, target market, and strategic context into your responses."
    return prompt


def format_conversation_messages(
    system_prompt: str,
    history: List[Dict[str, str]],
    user_message: str
) -> List[Dict[str, str]]:
    """Assemble the structured messages array for Groq chat completions API."""
    messages = [{"role": "system", "content": system_prompt}]

    for msg in history:
        role = msg.get("role")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})
    return messages


async def stream_groq_chat(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 4096
) -> AsyncGenerator[str, None]:
    """
    Stream chat completion tokens from Groq API using async Server-Sent Events.
    Yields text delta chunks as they arrive.
    """
    api_key = get_groq_api_key()
    if not api_key:
        raise AIConfigError(
            "Groq API key (GROQ_API_KEY) is not configured in backend/.env. "
            "Please set your GROQ_API_KEY to enable live AI responses."
        )

    selected_model = sanitize_model(model)
    endpoint = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": selected_model,
        "messages": messages,
        "stream": True,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    timeout = httpx.Timeout(connect=15.0, read=60.0, write=15.0, pool=15.0)

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream("POST", endpoint, headers=headers, json=payload) as response:
                if response.status_code in (401, 403):
                    raise AIAuthError("Invalid Groq API key or unauthorized. Please check your GROQ_API_KEY configuration.")
                if response.status_code == 429:
                    raise AIRateLimitError("Groq API rate limit exceeded. Please wait a moment and try again.")
                if response.status_code >= 400:
                    error_text = ""
                    async for chunk in response.aiter_text():
                        error_text += chunk
                    raise AIAPIError(f"Groq API returned status {response.status_code}: {error_text[:200]}", status_code=response.status_code)

                # Process SSE stream line by line
                buffer = ""
                async for chunk in response.aiter_text():
                    buffer += chunk
                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                return
                            try:
                                data_json = json.loads(data_str)
                                choices = data_json.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    content = delta.get("content")
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue

    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout) as conn_err:
        raise AIConnectionError(f"Failed to connect to Groq API: {str(conn_err)}")
    except httpx.HTTPError as http_err:
        raise AIError(f"HTTP error communicating with Groq: {str(http_err)}")


# Alias for backwards compatibility
stream_chat = stream_groq_chat
