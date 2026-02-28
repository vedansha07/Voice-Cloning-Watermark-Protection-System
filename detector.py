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
