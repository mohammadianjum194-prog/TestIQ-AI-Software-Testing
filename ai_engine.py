"""
ai_engine.py – AI abstraction layer for TestIQ.

Provides an AI-enhanced analysis path when an API key is configured,
and transparently falls back to the deterministic rule-based engine
(requirement_analyzer.py) when no key is present.

Design principles:
    - The caller never needs to know which engine is active.
    - Swapping the AI provider only requires changing this file.
    - API keys are loaded from environment variables only.
    - Failures in the AI path fall back gracefully to rule-based output.
"""

import json
import logging
from typing import Any, Dict

from config import AI_ENABLED, AI_PROVIDER, GEMINI_API_KEY, OPENAI_API_KEY, AI_MODEL
from requirement_analyzer import analyze_requirement as rule_based_analyze

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public entry-point
# ---------------------------------------------------------------------------

def ai_analyze_requirement(
    title: str,
    description: str,
    module: str = "",
    acceptance: str = "",
) -> Dict[str, Any]:
    """
    Analyse a requirement using AI if a key is configured,
    otherwise use the rule-based engine.

    Always returns the same dict schema as requirement_analyzer.analyze_requirement().
    """
    if not AI_ENABLED:
        logger.debug("AI disabled – using rule-based engine.")
        result = rule_based_analyze(title, description, module, acceptance)
        result["engine"] = "rule-based"
        return result

    try:
        if AI_PROVIDER == "openai" and OPENAI_API_KEY:
            result = _openai_analyze(title, description, module, acceptance)
        elif AI_PROVIDER == "gemini" and GEMINI_API_KEY:
            result = _gemini_analyze(title, description, module, acceptance)
        else:
            raise ValueError(f"Unsupported AI_PROVIDER: {AI_PROVIDER}")

        # Merge with rule-based output so structural fields are always present
        base = rule_based_analyze(title, description, module, acceptance)
        base.update(result)
        base["engine"] = f"ai:{AI_PROVIDER}"
        return base

    except Exception as exc:
        logger.warning("AI analysis failed (%s). Falling back to rule-based.", exc)
        result = rule_based_analyze(title, description, module, acceptance)
        result["engine"] = "rule-based (AI fallback)"
        return result


# ---------------------------------------------------------------------------
# OpenAI provider
# ---------------------------------------------------------------------------

def _openai_analyze(
    title: str, description: str, module: str, acceptance: str
) -> Dict[str, Any]:
    """Call the OpenAI Chat Completions API to enrich requirement analysis."""
    try:
        import openai  # optional dependency
    except ImportError as exc:
        raise ImportError(
            "openai package not installed. Run: pip install openai"
        ) from exc

    client = openai.OpenAI(api_key=OPENAI_API_KEY)

    prompt = _build_prompt(title, description, module, acceptance)

    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert software test engineer. "
                    "Analyse the given software requirement and return a JSON object "
                    "with keys: detected_fields (list), validation_rules (dict), "
                    "expected_behaviours (list), edge_cases (list), "
                    "boundary_conditions (list), potential_defects (list). "
                    "Return only valid JSON, no markdown."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
        max_tokens=1000,
    )

    raw = response.choices[0].message.content.strip()
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Gemini provider
# ---------------------------------------------------------------------------

def _gemini_analyze(
    title: str, description: str, module: str, acceptance: str
) -> Dict[str, Any]:
    """Call the Google Gemini API to enrich requirement analysis."""
    try:
        import google.generativeai as genai  # optional dependency
    except ImportError as exc:
        raise ImportError(
            "google-generativeai package not installed. "
            "Run: pip install google-generativeai"
        ) from exc

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-pro")

    prompt = _build_prompt(title, description, module, acceptance)
    full_prompt = (
        "You are an expert software test engineer. "
        "Analyse the following software requirement and return a JSON object "
        "with keys: detected_fields (list), validation_rules (dict), "
        "expected_behaviours (list), edge_cases (list), "
        "boundary_conditions (list), potential_defects (list). "
        "Return only valid JSON, no markdown fences.\n\n" + prompt
    )

    response = model.generate_content(full_prompt)
    raw = response.text.strip()
    # Strip markdown code fences if present
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-z]*\n?", "", raw)
        raw = raw.rstrip("`").strip()
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

import re  # noqa: E402 – imported here to keep top of file clean


def _build_prompt(title: str, description: str, module: str, acceptance: str) -> str:
    parts = [
        f"Title: {title}",
        f"Description: {description}",
    ]
    if module:
        parts.append(f"Module: {module}")
    if acceptance:
        parts.append(f"Acceptance Criteria:\n{acceptance}")
    return "\n".join(parts)


def get_engine_status() -> Dict[str, Any]:
    """Return a status dict describing which engine is active."""
    return {
        "ai_enabled": AI_ENABLED,
        "provider": AI_PROVIDER if AI_ENABLED else "none",
        "model": AI_MODEL if AI_ENABLED else "N/A",
        "mode": "AI-Enhanced" if AI_ENABLED else "Rule-Based (Offline)",
    }
