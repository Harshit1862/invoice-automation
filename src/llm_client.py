"""
Thin abstraction over the LLM provider. extraction.py and notifier.py call
these two functions and never touch a provider SDK directly -- switching
between Claude and Gemini is a one-line change in .env, not a code change.

Why this exists: Anthropic's API requires a paid credit balance with no
ongoing free tier. Google's Gemini API (via AI Studio) has a genuine free
tier -- no credit card required -- which is why this project defaults to
Gemini for development. Free-tier quotas are strict and shared per model,
so calls here retry with backoff on transient 429 (rate limit) and 503
(overloaded) errors instead of failing the whole batch on one hiccup.
"""
import time

from src import config


def _with_retry(func, max_attempts: int = 4, base_delay: int = 8):
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return func()
        except Exception as e:
            last_error = e
            if attempt == max_attempts:
                break
            delay = base_delay * (2 ** (attempt - 1))
            print(f"  [retry] call failed ({type(e).__name__}); waiting {delay}s before retry {attempt}/{max_attempts - 1}...")
            time.sleep(delay)
    raise last_error


def extract_json_from_pdf(pdf_path: str, prompt: str) -> str:
    """Sends a PDF + instruction prompt to the configured provider, returns raw text."""
    if config.LLM_PROVIDER == "gemini":
        return _gemini_pdf_call(pdf_path, prompt)
    return _anthropic_pdf_call(pdf_path, prompt)


def generate_text(prompt: str) -> str:
    """Sends a text-only prompt to the configured provider, returns raw text."""
    if config.LLM_PROVIDER == "gemini":
        return _gemini_text_call(prompt)
    return _anthropic_text_call(prompt)


# --- Gemini backend (free tier, default) ---

def _gemini_pdf_call(pdf_path: str, prompt: str) -> str:
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    def call():
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                prompt,
            ],
        )
        return response.text.strip()

    return _with_retry(call)


def _gemini_text_call(prompt: str) -> str:
    from google import genai

    client = genai.Client(api_key=config.GEMINI_API_KEY)

    def call():
        response = client.models.generate_content(
            model=config.GEMINI_MODEL,
            contents=prompt,
        )
        return response.text.strip()

    return _with_retry(call)


# --- Anthropic backend (swap to this once you have API credits) ---

def _anthropic_pdf_call(pdf_path: str, prompt: str) -> str:
    import base64
    import anthropic

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    with open(pdf_path, "rb") as f:
        pdf_b64 = base64.standard_b64encode(f.read()).decode("utf-8")

    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=1500,
        messages=[{
            "role": "user",
            "content": [
                {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": pdf_b64}},
                {"type": "text", "text": prompt},
            ],
        }],
    )
    return "".join(b.text for b in response.content if b.type == "text").strip()


def _anthropic_text_call(prompt: str) -> str:
    import anthropic

    client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    response = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return "".join(b.text for b in response.content if b.type == "text").strip()