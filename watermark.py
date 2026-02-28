import numpy as np
import librosa
import soundfile as sf

WATERMARK_SIGNATURE = [1, 0, 1, 1, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 1, 1]

N_FFT = 2048
HOP_LENGTH = 1024
START_BIN = 200
MODIFICATION_FACTOR = 0.18  # strong contrast


def embed_watermark(input_path: str, output_path: str) -> None:

    y, sr = librosa.load(input_path, sr=16000)

    stft_matrix = librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH)
    magnitude = np.abs(stft_matrix)
    phase = np.angle(stft_matrix)

    num_bins = magnitude.shape[0]

    for i, bit in enumerate(WATERMARK_SIGNATURE):

        bin_k = START_BIN + 2*i
        bin_k1 = bin_k + 1

        if bin_k1 < num_bins:

            if bit == 1:
                magnitude[bin_k, :] *= (1 + MODIFICATION_FACTOR)
                magnitude[bin_k1, :] *= (1 - MODIFICATION_FACTOR)
            else:
                magnitude[bin_k, :] *= (1 - MODIFICATION_FACTOR)
                magnitude[bin_k1, :] *= (1 + MODIFICATION_FACTOR)

    modified_stft = magnitude * np.exp(1j * phase)
    y_watermarked = librosa.istft(modified_stft, hop_length=HOP_LENGTH)

    max_val = np.max(np.abs(y_watermarked))
    if max_val > 0:
        y_watermarked = y_watermarked / max_val

    sf.write(output_path, y_watermarked, sr)


def detect_watermark(input_path: str) -> float:

    y, sr = librosa.load(input_path, sr=16000)

    stft_matrix = librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH)
    magnitude = np.abs(stft_matrix)

    num_bins = magnitude.shape[0]
    matched_bits = 0

    for i, expected_bit in enumerate(WATERMARK_SIGNATURE):

        bin_k = START_BIN + 2*i
        bin_k1 = bin_k + 1

        if bin_k1 < num_bins:

            mag_k = np.mean(magnitude[bin_k, :])
            mag_k1 = np.mean(magnitude[bin_k1, :])

            extracted_bit = 1 if mag_k > mag_k1 else 0

            if extracted_bit == expected_bit:
                matched_bits += 1

    return matched_bits / len(WATERMARK_SIGNATURE)