"""
llm_service.py — Gemini AI wrapper with fallback model chain.

All LLM interactions go through this service. No direct Gemini calls in agents.
"""

from google import genai
from google.genai import errors as genai_errors

from ..core.config import settings


# Create two isolated AI clients (Blue Team + Red Team)
client_blue = genai.Client(api_key=settings.GEMINI_API_KEY_BLUE)
client_red = genai.Client(api_key=settings.GEMINI_API_KEY_RED)


def generate_with_fallback(ai_client, prompt: str) -> str:
    """Try each model in the fallback chain. On 503, try the next."""
    for model_name in settings.FALLBACK_MODELS:
        try:
            print(f"    -> Trying {model_name}...")
            response = ai_client.models.generate_content(model=model_name, contents=prompt)
            return response.text.strip()
        except genai_errors.ServerError:
            print(f"    [!] {model_name} unavailable (503), falling back...")
            continue
    raise RuntimeError("All Gemini models are currently unavailable. Please try again later.")


def get_blue_client():
    """Return the Blue Team (defensive) AI client."""
    return client_blue


def get_red_client():
    """Return the Red Team (offensive) AI client."""
    return client_red
