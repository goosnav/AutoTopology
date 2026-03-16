"""VLM adapter — wraps llama-cpp-python for GGUF+MMProj inference.

Design:
- Lazy loading: model is not loaded at construction
- score_image: accepts PIL Image, runs prompt → parse with retry
- _run_inference: the sole point of contact with llama_cpp (mockable for tests)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from PIL import Image

from app.services.model_manager import ModelInfo
from vision.parsers.response_parser import VLMParseError, parse_vlm_response
from vision.prompts.scoring_prompt import build_retry_prompt, build_scoring_prompt


@dataclass
class VLMResult:
    """Result of a single VLM scoring call."""
    raw_text: str
    scores: dict[str, float]
    success: bool
    error: Optional[str] = None


class VLMAdapter:
    """Adapter wrapping a llama-cpp-python multimodal model.

    The underlying model is loaded lazily on first inference call.
    """

    def __init__(
        self,
        model_info: ModelInfo,
        n_ctx: int = 512,
        n_gpu_layers: int = 0,
        temperature: float = 0.1,
        max_retries: int = 2,
    ) -> None:
        self._model_info = model_info
        self._n_ctx = n_ctx
        self._n_gpu_layers = n_gpu_layers
        self._temperature = temperature
        self._max_retries = max_retries
        self._model = None  # Lazy
        self._ctx = None

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def _load(self) -> None:
        """Load the GGUF model and MMProj. Raises ImportError if llama_cpp unavailable."""
        try:
            from llama_cpp import Llama  # type: ignore
        except ImportError as e:
            raise ImportError(
                "llama-cpp-python is required for VLM inference. "
                "Install with: pip install llama-cpp-python"
            ) from e

        self._model = Llama(
            model_path=str(self._model_info.base_path),
            n_ctx=self._n_ctx,
            n_gpu_layers=self._n_gpu_layers,
            logits_all=False,
            verbose=False,
        )

    def _run_inference(
        self,
        prompt: str,
        image: Image.Image,
        temperature: Optional[float] = None,
    ) -> str:
        """Run a single inference pass. Returns raw model output text.

        This method is kept minimal and mockable. Actual llama_cpp calls happen here.
        """
        if not self.is_loaded:
            self._load()

        temp = temperature if temperature is not None else self._temperature

        # Convert PIL image to bytes for llama_cpp
        import io
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        image_bytes = buf.getvalue()

        # llama_cpp multimodal API
        from llama_cpp import Llama  # type: ignore
        # Create a chat completion with image
        result = self._model.create_chat_completion(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": "data:image/png;base64," + _b64(image_bytes)}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            temperature=temp,
            max_tokens=256,
        )
        return result["choices"][0]["message"]["content"]

    def score_image(self, image: Image.Image) -> VLMResult:
        """Score a PIL image. Retries with stricter prompt on parse failure.

        Returns:
            VLMResult with success=True and scores, or success=False with error.
        """
        prompts = [build_scoring_prompt()]
        if self._max_retries >= 1:
            prompts.append(build_retry_prompt())

        last_error: Optional[str] = None
        for attempt, prompt in enumerate(prompts):
            # Lower temperature on retries
            temp = self._temperature if attempt == 0 else max(0.0, self._temperature * 0.5)
            try:
                raw = self._run_inference(prompt, image, temperature=temp)
                scores = parse_vlm_response(raw)
                return VLMResult(raw_text=raw, scores=scores, success=True)
            except VLMParseError as exc:
                last_error = str(exc)
            except Exception as exc:  # inference errors
                last_error = str(exc)

        return VLMResult(raw_text="", scores={}, success=False, error=last_error)


def _b64(data: bytes) -> str:
    """Base64-encode bytes to string."""
    import base64
    return base64.b64encode(data).decode("ascii")
