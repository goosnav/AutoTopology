"""Tests for the exception hierarchy."""

from core.exceptions import (
    AutoTopologyError,
    BuildVolumeError,
    CheckpointError,
    ConfigValidationError,
    ExportError,
    GeometryGenerationError,
    MeshValidationError,
    ModelDiscoveryError,
    ModelInferenceError,
    PhysicsEvaluationError,
    RenderError,
    ScoringParseError,
    TasteModelError,
)

ALL_EXCEPTIONS = [
    ConfigValidationError,
    ModelDiscoveryError,
    ModelInferenceError,
    GeometryGenerationError,
    MeshValidationError,
    BuildVolumeError,
    PhysicsEvaluationError,
    RenderError,
    ScoringParseError,
    CheckpointError,
    ExportError,
    TasteModelError,
]


def test_base_exception_instantiable():
    err = AutoTopologyError("test error")
    assert str(err) == "test error"
    assert isinstance(err, Exception)


def test_base_exception_with_details():
    err = AutoTopologyError("test", details={"key": "value"})
    assert err.details == {"key": "value"}


def test_all_exceptions_inherit_from_base():
    for exc_class in ALL_EXCEPTIONS:
        err = exc_class("test")
        assert isinstance(err, AutoTopologyError)
        assert isinstance(err, Exception)


def test_all_exceptions_accept_message_and_details():
    for exc_class in ALL_EXCEPTIONS:
        err = exc_class("msg", details={"foo": "bar"})
        assert str(err) == "msg"
        assert err.details["foo"] == "bar"


def test_all_exceptions_details_default_empty():
    for exc_class in ALL_EXCEPTIONS:
        err = exc_class("msg")
        assert err.details == {}


def test_exception_count():
    assert len(ALL_EXCEPTIONS) == 12
