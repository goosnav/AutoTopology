"""Tests for logging service, model manager, and storage path manager."""

import json
from pathlib import Path

import pytest
from loguru import logger

from app.services.logging_service import setup_logging
from app.services.model_manager import (
    ModelInfo,
    get_model_by_name,
    scan_models,
    validate_models,
)
from config.schemas.config_models import LoggingConfig
from core.exceptions import ModelDiscoveryError
from storage.path_manager import StorageManager


# --- Logging Service ---

class TestLoggingService:
    def test_setup_creates_log_files(self, tmp_path):
        config = LoggingConfig(log_level="DEBUG", log_dir=tmp_path / "logs")
        setup_logging(config)
        logger.info("test message")
        # Force flush
        logger.complete()

        log_dir = tmp_path / "logs"
        assert log_dir.exists()
        log_file = log_dir / "autotopology.log"
        jsonl_file = log_dir / "autotopology.jsonl"
        assert log_file.exists()
        assert jsonl_file.exists()

    def test_log_message_in_file_sink(self, tmp_path):
        config = LoggingConfig(log_level="DEBUG", log_dir=tmp_path / "logs")
        setup_logging(config)
        logger.info("hello from test")
        logger.complete()

        content = (tmp_path / "logs" / "autotopology.log").read_text()
        assert "hello from test" in content

    def test_log_message_in_json_sink(self, tmp_path):
        config = LoggingConfig(log_level="DEBUG", log_dir=tmp_path / "logs")
        setup_logging(config)
        logger.info("json test msg")
        logger.complete()

        content = (tmp_path / "logs" / "autotopology.jsonl").read_text()
        for line in content.strip().split("\n"):
            record = json.loads(line)
            if "json test msg" in record.get("text", ""):
                break
        else:
            pytest.fail("Message not found in JSON log")


# --- Model Manager ---

class TestModelManager:
    def _create_model_dir(self, base: Path, name: str, model_file: str, mmproj_file: str):
        d = base / name
        d.mkdir(parents=True)
        (d / model_file).write_bytes(b"\x00" * 100)
        (d / mmproj_file).write_bytes(b"\x00" * 50)
        return d

    def test_scan_finds_models(self, tmp_path):
        self._create_model_dir(tmp_path, "moondream2",
                               "moondream2-text-model.gguf", "moondream2-mmproj.gguf")
        models = scan_models(tmp_path)
        assert len(models) == 1
        assert models[0].name == "moondream2"
        assert models[0].compatible

    def test_scan_finds_multiple_models(self, tmp_path):
        self._create_model_dir(tmp_path, "moondream2",
                               "moondream2-text-model.gguf", "moondream2-mmproj.gguf")
        self._create_model_dir(tmp_path, "paddleocr-vl",
                               "PaddleOCR-VL.gguf", "mmproj-F32.gguf")
        models = scan_models(tmp_path)
        assert len(models) == 2
        names = {m.name for m in models}
        assert "moondream2" in names
        assert "paddleocr-vl" in names

    def test_scan_missing_mmproj_marks_incompatible(self, tmp_path):
        d = tmp_path / "bad_model"
        d.mkdir()
        (d / "model.gguf").write_bytes(b"\x00" * 100)
        models = scan_models(tmp_path)
        assert len(models) == 1
        assert not models[0].compatible

    def test_scan_empty_dir_returns_empty(self, tmp_path):
        models = scan_models(tmp_path)
        assert models == []

    def test_scan_missing_dir_raises(self):
        with pytest.raises(ModelDiscoveryError):
            scan_models(Path("/nonexistent/models"))

    def test_validate_models_passes_with_compatible(self, tmp_path):
        self._create_model_dir(tmp_path, "moondream2",
                               "model.gguf", "mmproj.gguf")
        models = scan_models(tmp_path)
        valid = validate_models(models)
        assert len(valid) == 1

    def test_validate_models_raises_when_none_compatible(self, tmp_path):
        d = tmp_path / "bad"
        d.mkdir()
        (d / "model.gguf").write_bytes(b"\x00")
        models = scan_models(tmp_path)
        with pytest.raises(ModelDiscoveryError):
            validate_models(models)

    def test_get_model_by_name(self, tmp_path):
        self._create_model_dir(tmp_path, "moondream2",
                               "model.gguf", "mmproj.gguf")
        models = scan_models(tmp_path)
        m = get_model_by_name(models, "moondream2")
        assert m.name == "moondream2"

    def test_get_model_by_name_not_found(self, tmp_path):
        self._create_model_dir(tmp_path, "moondream2",
                               "model.gguf", "mmproj.gguf")
        models = scan_models(tmp_path)
        with pytest.raises(ModelDiscoveryError):
            get_model_by_name(models, "nonexistent")


# --- Storage Path Manager ---

class TestStorageManager:
    def test_resolve_paths(self, tmp_path):
        sm = StorageManager(tmp_path)
        assert sm.root == tmp_path.resolve()
        assert sm.checkpoints == tmp_path.resolve() / "storage" / "checkpoints"
        assert sm.cache == tmp_path.resolve() / "storage" / "cache"
        assert sm.exports == tmp_path.resolve() / "storage" / "exports"

    def test_ensure_dirs_creates_all(self, tmp_path):
        sm = StorageManager(tmp_path)
        sm.ensure_dirs()
        for subdir in StorageManager.SUBDIRS:
            assert (tmp_path / "storage" / subdir).is_dir()

    def test_resolve_path_within_root(self, tmp_path):
        sm = StorageManager(tmp_path)
        p = sm.resolve_path("storage/cache/test.png")
        assert str(p).startswith(str(tmp_path.resolve()))

    def test_resolve_path_traversal_raises(self, tmp_path):
        sm = StorageManager(tmp_path)
        with pytest.raises(ValueError, match="Path traversal"):
            sm.resolve_path("../../etc/passwd")

    def test_sanitize_filename_strips_path(self):
        assert StorageManager.sanitize_filename("/etc/passwd") == "passwd"
        assert StorageManager.sanitize_filename("../../../etc/shadow") == "shadow"

    def test_sanitize_filename_strips_unsafe_chars(self):
        result = StorageManager.sanitize_filename("file name!@#$.stl")
        assert "!" not in result
        assert "@" not in result
        assert " " not in result
        assert result.endswith(".stl")

    def test_sanitize_filename_strips_leading_dots(self):
        assert StorageManager.sanitize_filename(".hidden") == "hidden"

    def test_sanitize_filename_empty_fallback(self):
        assert StorageManager.sanitize_filename("...") == "unnamed"
