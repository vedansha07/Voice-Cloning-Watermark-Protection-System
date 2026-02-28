"""
detector.py

Deepfake detection module for VoiceGuard.
Wraps a pretrained Hugging Face Wav2Vec2-based model into a reusable class.
"""

import os
import tempfile
from typing import Tuple

import librosa
from transformers import pipeline


class DeepfakeDetector:
    """
    DeepfakeDetector wraps a pre-trained Hugging Face audio classification model
    (garystafford/wav2vec2-deepfake-voice-detector) into a reusable component.
    """

    def __init__(self) -> None:
        """
        Initializes the DeepfakeDetector.
        The Hugging Face pipeline and model are loaded only once during construction
        to ensure efficient inference on subsequent calls.
        """
        self.model_id = "garystafford/wav2vec2-deepfake-voice-detector"
        self.target_sr = 16000

        try:
            self.classifier = pipeline(
                "audio-classification",
                model=self.model_id
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to load Hugging Face model '{self.model_id}': {e}"
            )

    def detect(self, audio_bytes: bytes, suffix: str = ".wav") -> Tuple[str, float]:
        """
        Processes an audio file to determine if it is a deepfake.

        Args:
            audio_bytes (bytes): Raw bytes of uploaded audio file.
            suffix (str): File extension (e.g., '.wav', '.mp3').

        Returns:
            Tuple[str, float]:
                - label (str): Predicted class ('real' or 'fake')
                - confidence (float): Probability score (0.0 - 1.0)
        """
        temp_filepath = None

        try:
            # Save uploaded audio to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(audio_bytes)
                temp_filepath = temp_file.name

            # Load and resample audio to 16kHz
            audio_array, _ = librosa.load(
                temp_filepath,
                sr=self.target_sr
            )

            # Run inference
            results = self.classifier({
                "raw": audio_array,
                "sampling_rate": self.target_sr
            })

            if not results:
                raise ValueError("Model returned empty result.")

            top_prediction = results[0]
            label = str(top_prediction.get("label", "unknown"))
            confidence = float(top_prediction.get("score", 0.0))

            return label, confidence

        except Exception as e:
            raise ValueError(f"Error during deepfake detection: {e}")

        finally:
            # Cleanup temp file
            if temp_filepath and os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except OSError:
                    pass