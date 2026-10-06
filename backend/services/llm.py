import logging
from typing import TypeVar

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, ValidationError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from backend import config

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Raised when the LLM call fails in a way the caller should handle."""
_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    if _client is None:
        if not config.GEMINI_API_KEY:
            raise LLMError("GEMINI_API_KEY is not set")
        _client = genai.Client(
            api_key=config.GEMINI_API_KEY,
            http_options=types.HttpOptions(timeout=30_000),
        )
    return _client

def _is_transient(exc: BaseException) -> bool:
    return isinstance(exc, errors.APIError) and exc.code in {429, 500, 502, 503, 504}


@retry(
    retry=retry_if_exception(_is_transient),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    reraise=True,
)
def _call(contents: str, cfg: types.GenerateContentConfig):
    return get_client().models.generate_content(
        model=config.GEMINI_MODEL, contents=contents, config=cfg
    )

def generate_text(prompt: str, system: str | None = None, temperature: float = 0.2) -> str:
    cfg = types.GenerateContentConfig(system_instruction=system, temperature=temperature)
    try:
        response = _call(prompt, cfg)
    except errors.APIError as exc:
        logger.exception("Gemini API error")
        raise LLMError(f"Gemini API error {exc.code}") from exc
    if not response.text:
        raise LLMError("Empty response (possibly blocked by safety filters)")
    return response.text

def generate_structured(prompt: str, schema: type[T], system: str | None = None) -> T:
    cfg = types.GenerateContentConfig(
        system_instruction=system,
        temperature=0,
        response_mime_type="application/json",
        response_schema=schema,
    )
    try:
        response = _call(prompt, cfg)
    except errors.APIError as exc:
        logger.exception("Gemini API error")
        raise LLMError(f"Gemini API error {exc.code}") from exc

    if not response.text:
        raise LLMError("Empty response (possibly blocked by safety filters)")
    try:
        return schema.model_validate_json(response.text)
    except ValidationError as exc:
        logger.exception("Model output did not match schema")
        raise LLMError("Model returned invalid structured output") from exc