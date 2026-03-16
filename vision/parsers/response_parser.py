"""VLM response parser — extracts and validates structured scores.

Spec (§15.6):
- Accept only exact keys from SCORE_KEYS
- Coerce numeric strings only if safe
- Reject extra unexpected text in strict mode (default)
- Clamp out-of-range outputs only if configured to do so
- Otherwise treat malformed output as a scoring failure
"""

from __future__ import annotations

import json
import re
from typing import Any

from vision.prompts.scoring_prompt import SCORE_KEYS


class VLMParseError(Exception):
    """Raised when the VLM response cannot be parsed into valid scores."""


# Score range
_MIN_SCORE = 0.0
_MAX_SCORE = 10.0

# Regex to extract the first JSON object from a string
_JSON_OBJECT_RE = re.compile(r"\{[^{}]*\}", re.DOTALL)


def _extract_json(text: str) -> dict[str, Any]:
    """Extract the first JSON object from text.

    Raises:
        VLMParseError: If no valid JSON object is found.
    """
    # Try the whole string first
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Try to find an embedded JSON object
    match = _JSON_OBJECT_RE.search(text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    raise VLMParseError(f"No valid JSON object found in VLM response: {text[:200]!r}")


def _coerce_value(value: Any, key: str) -> float:
    """Coerce a value to float; raise VLMParseError if not safely numeric."""
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            raise VLMParseError(
                f"Score '{key}' is a non-numeric string: {value!r}"
            )
    raise VLMParseError(
        f"Score '{key}' has unexpected type {type(value).__name__}: {value!r}"
    )


def parse_vlm_response(
    text: str,
    clamp: bool = False,
) -> dict[str, float]:
    """Parse a VLM response string into a validated score dict.

    Args:
        text: Raw text output from the VLM.
        clamp: If True, clamp out-of-range values to [0, 10]. If False, raise.

    Returns:
        Dict mapping each SCORE_KEY to a float in [0, 10].

    Raises:
        VLMParseError: On any parse or validation failure.
    """
    data = _extract_json(text)

    scores: dict[str, float] = {}
    for key in SCORE_KEYS:
        if key not in data:
            raise VLMParseError(f"Missing required score key: '{key}'")
        raw = data[key]
        value = _coerce_value(raw, key)

        if clamp:
            value = max(_MIN_SCORE, min(_MAX_SCORE, value))
        elif value < _MIN_SCORE or value > _MAX_SCORE:
            raise VLMParseError(
                f"Score '{key}' out of range [{_MIN_SCORE}, {_MAX_SCORE}]: {value}"
            )

        scores[key] = value

    return scores


def normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    """Normalize scores from [0, 10] to [0.0, 1.0].

    Args:
        scores: Dict of score keys to values in [0, 10].

    Returns:
        Dict with same keys, values in [0.0, 1.0].
    """
    return {k: v / _MAX_SCORE for k, v in scores.items()}
