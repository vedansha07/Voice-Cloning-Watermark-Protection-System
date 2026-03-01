import os
import tempfile
from typing import Tuple
import librosa
from transformers import pipeline

class DeepfakeDetector:

    def __init__(self) -> None:
        self.model_id = 'garystafford/wav2vec2-deepfake-voice-detector'
        self.target_sr = 16000
        try:
            self.classifier = pipeline('audio-classification', model=self.model_id)
        except Exception as e:
            raise RuntimeError(f"Failed to load Hugging Face model '{self.model_id}': {e}")

    def detect(self, audio_bytes: bytes, suffix: str='.wav') -> Tuple[str, float]:
        temp_filepath = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(audio_bytes)
                temp_filepath = temp_file.name
            audio_array, _ = librosa.load(temp_filepath, sr=self.target_sr)
            results = self.classifier({'raw': audio_array, 'sampling_rate': self.target_sr})
            if not results:
                raise ValueError('Model returned empty result.')
            top_prediction = results[0]
            label = str(top_prediction.get('label', 'unknown'))
            confidence = float(top_prediction.get('score', 0.0))
            return (label, confidence)
        except Exception as e:
            raise ValueError(f'Error during deepfake detection: {e}')
        finally:
            if temp_filepath and os.path.exists(temp_filepath):
                try:
                    os.remove(temp_filepath)
                except OSError:
                    pass
