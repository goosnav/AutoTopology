"""Tests for dev_cli.py."""

from typer.testing import CliRunner

from dev_cli import app

runner = CliRunner()


def test_cli_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "AutoTopology" in result.output


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_validate_config_default():
    result = runner.invoke(app, ["validate-config"])
    assert result.exit_code == 0
    assert "Config valid" in result.output


def test_validate_config_invalid(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("ea:\n  population_count: -1\n")
    result = runner.invoke(app, ["validate-config", "--config", str(bad)])
    assert result.exit_code == 1


def test_scan_models():
    result = runner.invoke(app, ["scan-models", "--models-dir", "models"])
    assert result.exit_code == 0
    assert "paddleocr-vl" in result.output


def test_cli_lists_all_commands():
    result = runner.invoke(app, ["--help"])
    expected_commands = [
        "validate-config",
        "scan-models",
        "test-model-inference",
        "generate-candidate-once",
        "render-candidate-once",
        "evaluate-physics-once",
        "score-candidate-once",
        "run-generation-once",
        "run-project",
        "resume-project",
        "export-candidate",
        "cleanup-cache",
        "train-taste-model",
        "run-smoke-test",
    ]
    for cmd in expected_commands:
        assert cmd in result.output, f"Command '{cmd}' not found in CLI help"


def test_stubbed_command_exits_cleanly():
    result = runner.invoke(app, ["test-model-inference"])
    assert result.exit_code == 0
    assert "Not implemented yet" in result.output
