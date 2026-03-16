"""Phase 4 VLM scoring tests — prompts, parser, loader, orchestrator."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import tempfile
import pytest
from PIL import Image


# ---------------------------------------------------------------------------
# vision/prompts/scoring_prompt.py
# ---------------------------------------------------------------------------

class TestScoringPrompt:
    def test_build_prompt_returns_string(self):
        from vision.prompts.scoring_prompt import build_scoring_prompt
        result = build_scoring_prompt()
        assert isinstance(result, str)
        assert len(result) > 50

    def test_prompt_contains_all_score_keys(self):
        from vision.prompts.scoring_prompt import build_scoring_prompt, SCORE_KEYS
        prompt = build_scoring_prompt()
        for key in SCORE_KEYS:
            assert key in prompt

    def test_score_keys_are_expected(self):
        from vision.prompts.scoring_prompt import SCORE_KEYS
        expected = {
            "aesthetic_coherence",
            "proportion_balance",
            "novelty_interest",
            "style_match",
            "plausibility_of_form",
            "visual_resolution",
            "overall",
        }
        assert set(SCORE_KEYS) == expected

    def test_retry_prompt_is_stricter(self):
        from vision.prompts.scoring_prompt import build_scoring_prompt, build_retry_prompt
        base = build_scoring_prompt()
        retry = build_retry_prompt()
        assert isinstance(retry, str)
        # Retry prompt must be non-empty and different from base
        assert len(retry) > 0
        assert retry != base

    def test_build_schema_dict(self):
        from vision.prompts.scoring_prompt import build_response_schema
        schema = build_response_schema()
        assert isinstance(schema, dict)
        assert "aesthetic_coherence" in schema
        assert "overall" in schema


# ---------------------------------------------------------------------------
# vision/parsers/response_parser.py
# ---------------------------------------------------------------------------

VALID_RESPONSE = json.dumps({
    "aesthetic_coherence": 7,
    "proportion_balance": 6,
    "novelty_interest": 8,
    "style_match": 5,
    "plausibility_of_form": 7,
    "visual_resolution": 6,
    "overall": 7,
})

class TestResponseParser:
    def test_parse_valid_json_response(self):
        from vision.parsers.response_parser import parse_vlm_response
        result = parse_vlm_response(VALID_RESPONSE)
        assert result["overall"] == 7
        assert result["aesthetic_coherence"] == 7

    def test_parse_extracts_json_from_surrounding_text(self):
        from vision.parsers.response_parser import parse_vlm_response
        wrapped = f"Here is the result:\n{VALID_RESPONSE}\nDone."
        result = parse_vlm_response(wrapped)
        assert result["overall"] == 7

    def test_parse_rejects_missing_keys(self):
        from vision.parsers.response_parser import parse_vlm_response, VLMParseError
        bad = json.dumps({"aesthetic_coherence": 7})
        with pytest.raises(VLMParseError):
            parse_vlm_response(bad)

    def test_parse_rejects_out_of_range_strict(self):
        from vision.parsers.response_parser import parse_vlm_response, VLMParseError
        data = json.loads(VALID_RESPONSE)
        data["overall"] = 15  # > 10
        with pytest.raises(VLMParseError):
            parse_vlm_response(json.dumps(data), clamp=False)

    def test_parse_clamps_out_of_range_when_configured(self):
        from vision.parsers.response_parser import parse_vlm_response
        data = json.loads(VALID_RESPONSE)
        data["overall"] = 15
        result = parse_vlm_response(json.dumps(data), clamp=True)
        assert result["overall"] == 10

    def test_parse_coerces_numeric_strings(self):
        from vision.parsers.response_parser import parse_vlm_response
        data = {k: str(v) for k, v in json.loads(VALID_RESPONSE).items()}
        result = parse_vlm_response(json.dumps(data))
        assert isinstance(result["overall"], (int, float))

    def test_parse_raises_on_garbage_text(self):
        from vision.parsers.response_parser import parse_vlm_response, VLMParseError
        with pytest.raises(VLMParseError):
            parse_vlm_response("This is not JSON at all.")

    def test_parse_rejects_unexpected_value_types(self):
        from vision.parsers.response_parser import parse_vlm_response, VLMParseError
        data = json.loads(VALID_RESPONSE)
        data["overall"] = "excellent"
        with pytest.raises(VLMParseError):
            parse_vlm_response(json.dumps(data))

    def test_normalize_scores_to_0_1(self):
        from vision.parsers.response_parser import parse_vlm_response, normalize_scores
        raw = parse_vlm_response(VALID_RESPONSE)
        normalized = normalize_scores(raw)
        for v in normalized.values():
            assert 0.0 <= v <= 1.0


# ---------------------------------------------------------------------------
# vision/adapters/vlm_loader.py
# ---------------------------------------------------------------------------

class TestVLMLoader:
    def test_vlm_loader_exists(self):
        from vision.adapters import vlm_loader  # noqa: F401

    def test_vlm_result_dataclass(self):
        from vision.adapters.vlm_loader import VLMResult
        r = VLMResult(raw_text="hello", scores={"overall": 7.0}, success=True)
        assert r.success
        assert r.raw_text == "hello"

    def test_vlm_result_failure(self):
        from vision.adapters.vlm_loader import VLMResult
        r = VLMResult(raw_text="", scores={}, success=False, error="timeout")
        assert not r.success
        assert r.error == "timeout"

    def test_vlm_adapter_interface(self):
        """VLMAdapter must have score_image method."""
        from vision.adapters.vlm_loader import VLMAdapter
        adapter = VLMAdapter.__new__(VLMAdapter)
        assert hasattr(adapter, "score_image")

    def test_vlm_adapter_not_loaded_on_init(self):
        """Adapter should be lazy — model not loaded at construction."""
        from vision.adapters.vlm_loader import VLMAdapter
        from app.services.model_manager import ModelInfo
        info = ModelInfo(
            name="test",
            base_path=Path("/fake/model.gguf"),
            mmproj_path=Path("/fake/mmproj.gguf"),
        )
        adapter = VLMAdapter(info, n_ctx=512, n_gpu_layers=0, temperature=0.1)
        assert not adapter.is_loaded

    def test_vlm_adapter_score_image_mocked(self):
        """score_image should call _run_inference and parse result."""
        from vision.adapters.vlm_loader import VLMAdapter, VLMResult
        from app.services.model_manager import ModelInfo
        info = ModelInfo(
            name="test",
            base_path=Path("/fake/model.gguf"),
            mmproj_path=Path("/fake/mmproj.gguf"),
        )
        adapter = VLMAdapter(info, n_ctx=512, n_gpu_layers=0, temperature=0.1)
        img = Image.new("RGB", (64, 64), color=(200, 200, 200))

        with patch.object(adapter, "_run_inference", return_value=VALID_RESPONSE):
            result = adapter.score_image(img)

        assert isinstance(result, VLMResult)
        assert result.success
        assert "overall" in result.scores

    def test_vlm_adapter_score_image_parse_failure(self):
        """score_image returns failure VLMResult when parse fails."""
        from vision.adapters.vlm_loader import VLMAdapter, VLMResult
        from app.services.model_manager import ModelInfo
        info = ModelInfo(
            name="test",
            base_path=Path("/fake/model.gguf"),
            mmproj_path=Path("/fake/mmproj.gguf"),
        )
        adapter = VLMAdapter(info, n_ctx=512, n_gpu_layers=0, temperature=0.1)
        img = Image.new("RGB", (64, 64))

        with patch.object(adapter, "_run_inference", return_value="not json"):
            result = adapter.score_image(img)

        assert isinstance(result, VLMResult)
        assert not result.success

    def test_vlm_adapter_retry_on_first_parse_failure(self):
        """score_image retries with stricter prompt when first attempt fails."""
        from vision.adapters.vlm_loader import VLMAdapter
        from app.services.model_manager import ModelInfo
        info = ModelInfo(
            name="test",
            base_path=Path("/fake/model.gguf"),
            mmproj_path=Path("/fake/mmproj.gguf"),
        )
        adapter = VLMAdapter(info, n_ctx=512, n_gpu_layers=0, temperature=0.1, max_retries=1)
        img = Image.new("RGB", (64, 64))

        call_count = {"n": 0}
        def fake_inference(prompt, image, temperature=None):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return "not json"
            return VALID_RESPONSE

        with patch.object(adapter, "_run_inference", side_effect=fake_inference):
            result = adapter.score_image(img)

        assert result.success
        assert call_count["n"] == 2


# ---------------------------------------------------------------------------
# vision/scoring/score_orchestrator.py
# ---------------------------------------------------------------------------

class TestScoreOrchestrator:
    def _make_orchestrator(self, fallback_mode="physics_only"):
        from vision.scoring.score_orchestrator import ScoreOrchestrator
        mock_adapter = MagicMock()
        return ScoreOrchestrator(
            adapter=mock_adapter,
            cache_dir=None,
            failure_rate_threshold=0.5,
            fallback_mode=fallback_mode,
        )

    def test_orchestrator_score_returns_dict(self):
        from vision.scoring.score_orchestrator import ScoreOrchestrator
        from vision.adapters.vlm_loader import VLMResult
        mock_adapter = MagicMock()
        mock_adapter.score_image.return_value = VLMResult(
            raw_text=VALID_RESPONSE,
            scores=json.loads(VALID_RESPONSE),
            success=True,
        )
        orch = ScoreOrchestrator(
            adapter=mock_adapter,
            cache_dir=None,
            failure_rate_threshold=0.5,
            fallback_mode="physics_only",
        )
        img = Image.new("RGB", (128, 128))
        result = orch.score(img, candidate_hash="abc123")
        assert isinstance(result, dict)
        assert "overall" in result

    def test_orchestrator_caches_result(self):
        from vision.scoring.score_orchestrator import ScoreOrchestrator
        from vision.adapters.vlm_loader import VLMResult
        mock_adapter = MagicMock()
        mock_adapter.score_image.return_value = VLMResult(
            raw_text=VALID_RESPONSE,
            scores=json.loads(VALID_RESPONSE),
            success=True,
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            orch = ScoreOrchestrator(
                adapter=mock_adapter,
                cache_dir=Path(tmpdir),
                failure_rate_threshold=0.5,
                fallback_mode="physics_only",
            )
            img = Image.new("RGB", (128, 128))
            orch.score(img, candidate_hash="abc123")
            # Second call should not invoke adapter again
            orch.score(img, candidate_hash="abc123")
            assert mock_adapter.score_image.call_count == 1

    def test_orchestrator_returns_none_on_failure_physics_only(self):
        from vision.scoring.score_orchestrator import ScoreOrchestrator
        from vision.adapters.vlm_loader import VLMResult
        mock_adapter = MagicMock()
        mock_adapter.score_image.return_value = VLMResult(
            raw_text="", scores={}, success=False, error="bad parse"
        )
        orch = ScoreOrchestrator(
            adapter=mock_adapter,
            cache_dir=None,
            failure_rate_threshold=0.5,
            fallback_mode="physics_only",
        )
        img = Image.new("RGB", (128, 128))
        result = orch.score(img, candidate_hash="xyz")
        assert result is None

    def test_orchestrator_raises_on_failure_fail_mode(self):
        from vision.scoring.score_orchestrator import ScoreOrchestrator, VLMScoringError
        from vision.adapters.vlm_loader import VLMResult
        mock_adapter = MagicMock()
        mock_adapter.score_image.return_value = VLMResult(
            raw_text="", scores={}, success=False, error="bad parse"
        )
        orch = ScoreOrchestrator(
            adapter=mock_adapter,
            cache_dir=None,
            failure_rate_threshold=0.5,
            fallback_mode="fail",
        )
        img = Image.new("RGB", (128, 128))
        with pytest.raises(VLMScoringError):
            orch.score(img, candidate_hash="xyz")

    def test_orchestrator_tracks_failure_rate(self):
        from vision.scoring.score_orchestrator import ScoreOrchestrator, VLMScoringError
        from vision.adapters.vlm_loader import VLMResult
        mock_adapter = MagicMock()
        mock_adapter.score_image.return_value = VLMResult(
            raw_text="", scores={}, success=False, error="bad"
        )
        orch = ScoreOrchestrator(
            adapter=mock_adapter,
            cache_dir=None,
            failure_rate_threshold=0.5,
            fallback_mode="physics_only",
        )
        img = Image.new("RGB", (128, 128))
        # Exceed failure threshold (3 failures, 0 successes → 100% > 50%)
        for i in range(3):
            orch.score(img, candidate_hash=f"h{i}")

        with pytest.raises(VLMScoringError, match="failure rate"):
            orch.score(img, candidate_hash="final")

    def test_orchestrator_uses_cached_fallback(self):
        from vision.scoring.score_orchestrator import ScoreOrchestrator
        from vision.adapters.vlm_loader import VLMResult
        mock_adapter = MagicMock()
        good_scores = json.loads(VALID_RESPONSE)

        call_count = {"n": 0}
        def side_effect(img):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return VLMResult(raw_text=VALID_RESPONSE, scores=good_scores, success=True)
            return VLMResult(raw_text="", scores={}, success=False, error="bad")

        mock_adapter.score_image.side_effect = side_effect
        with tempfile.TemporaryDirectory() as tmpdir:
            orch = ScoreOrchestrator(
                adapter=mock_adapter,
                cache_dir=Path(tmpdir),
                failure_rate_threshold=0.5,
                fallback_mode="cached",
            )
            img = Image.new("RGB", (128, 128))
            # Prime the cache
            first = orch.score(img, candidate_hash="abc")
            assert first is not None
            # Now fail but same hash → should return cached
            result = orch.score(img, candidate_hash="abc")
            assert result == first

    def test_orchestrator_reset_clears_failure_counts(self):
        from vision.scoring.score_orchestrator import ScoreOrchestrator
        from vision.adapters.vlm_loader import VLMResult
        mock_adapter = MagicMock()
        mock_adapter.score_image.return_value = VLMResult(
            raw_text="", scores={}, success=False, error="bad"
        )
        orch = ScoreOrchestrator(
            adapter=mock_adapter,
            cache_dir=None,
            failure_rate_threshold=0.5,
            fallback_mode="physics_only",
        )
        img = Image.new("RGB", (128, 128))
        for i in range(3):
            orch.score(img, candidate_hash=f"h{i}")
        orch.reset_stats()
        assert orch.failure_count == 0
        assert orch.total_count == 0
