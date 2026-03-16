"""Structured scoring prompts for VLM aesthetic evaluation.

The VLM is asked to return only a JSON object with fixed keys; no free-text.
"""

from __future__ import annotations

# Canonical score keys — order is stable (used for schema and parser)
SCORE_KEYS: list[str] = [
    "aesthetic_coherence",
    "proportion_balance",
    "novelty_interest",
    "style_match",
    "plausibility_of_form",
    "visual_resolution",
    "overall",
]

_SCHEMA_DESCRIPTION = "\n".join(
    f'  "{k}": <integer 0-10>' for k in SCORE_KEYS
)

_BASE_PROMPT = f"""\
You are an expert industrial designer evaluating a 3D furniture candidate shown in a 4-view collage.

Rate the object on each of the following axes using an integer from 0 (worst) to 10 (best).
Return ONLY a valid JSON object — no explanations, no extra keys, no markdown.

Required JSON schema:
{{
{_SCHEMA_DESCRIPTION}
}}

Scoring guide:
- aesthetic_coherence: Does the overall form feel unified and purposeful?
- proportion_balance: Are the parts well-proportioned relative to each other?
- novelty_interest: Is the design visually interesting or original?
- style_match: Does it resemble a coherent design style (minimalist, organic, etc.)?
- plausibility_of_form: Does it look like a real, functional object?
- visual_resolution: Is the silhouette clean and resolved, without chaotic noise?
- overall: Your holistic rating weighing all factors.

Respond with ONLY the JSON object, starting with {{ and ending with }}.
"""

_RETRY_PROMPT = f"""\
STRICT MODE. You must respond with ONLY a valid JSON object and nothing else.

Rate this 3D furniture image on these axes (integer 0-10 each):
{', '.join(SCORE_KEYS)}

Your response must be exactly this format — no prefix, no suffix, no markdown:
{{
{_SCHEMA_DESCRIPTION}
}}

Start your response with the {{ character.
"""


def build_scoring_prompt() -> str:
    """Return the base scoring prompt."""
    return _BASE_PROMPT


def build_retry_prompt() -> str:
    """Return a stricter scoring prompt for retry attempts."""
    return _RETRY_PROMPT


def build_response_schema() -> dict[str, str]:
    """Return a dict describing the expected response schema."""
    return {k: "integer 0-10" for k in SCORE_KEYS}
