"""AutoTopology exception hierarchy.

All subsystem exceptions inherit from AutoTopologyError.
Each accepts a message and optional details dict for structured error context.
"""


class AutoTopologyError(Exception):
    """Base exception for all AutoTopology errors."""

    def __init__(self, message: str, *, details: dict | None = None):
        super().__init__(message)
        self.details = details or {}


class ConfigValidationError(AutoTopologyError):
    """Raised when config validation fails."""


class ModelDiscoveryError(AutoTopologyError):
    """Raised when model files cannot be found or paired."""


class ModelInferenceError(AutoTopologyError):
    """Raised when VLM inference fails."""


class GeometryGenerationError(AutoTopologyError):
    """Raised when geometry generation fails for a candidate."""


class MeshValidationError(AutoTopologyError):
    """Raised when mesh validation detects invalid geometry."""


class BuildVolumeError(AutoTopologyError):
    """Raised when a candidate exceeds printer build volume."""


class PhysicsEvaluationError(AutoTopologyError):
    """Raised when physics evaluation fails."""


class RenderError(AutoTopologyError):
    """Raised when candidate rendering fails."""


class ScoringParseError(AutoTopologyError):
    """Raised when VLM scoring output cannot be parsed."""


class CheckpointError(AutoTopologyError):
    """Raised when checkpoint save or load fails."""


class ExportError(AutoTopologyError):
    """Raised when candidate export fails."""


class TasteModelError(AutoTopologyError):
    """Raised when taste model operations fail (non-critical)."""
