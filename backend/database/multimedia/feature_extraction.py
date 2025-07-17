import librosa
import numpy as np
import os
import sys
from global_utils import Utils
from logger import Logger

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def extract_features(audio_path,n_mfcc=13, frame_length=2048, hop_length=512):
    """
    Extrae descriptores locales MFCC, delta y delta-delta de un archivo de audio.

    Args:
        audio_path (str): Ruta al archivo de audio.
        n_mfcc (int): Número de coeficientes MFCC a extraer (por frame).
        frame_length (int): Tamaño de ventana para análisis de STFT.
        hop_length (int): Paso entre ventanas para STFT.

    Returns:
        np.ndarray: Matriz de características locales con forma (n_frames, n_features).
                    n_features = n_mfcc * 3 (MFCC + delta + delta-delta).
    """
    try:
        audio_path = Utils.build_path("sounds", audio_path)

        # Carga audio en mono y frecuencia original
        y, sr = librosa.load(audio_path, sr=None, mono=True)

        # Extraer MFCCs: shape (n_mfcc, n_frames)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc,
                                     n_fft=frame_length, hop_length=hop_length)

        # Extraer delta y delta-delta (derivadas de MFCC)
        delta_mfccs = librosa.feature.delta(mfccs)
        delta2_mfccs = librosa.feature.delta(mfccs, order=2)

        # Transponer para que cada fila sea un vector descriptor local (por frame)
        mfccs = mfccs.T           # shape (n_frames, n_mfcc)
        delta_mfccs = delta_mfccs.T
        delta2_mfccs = delta2_mfccs.T

        # Concatenar vectores locales en cada frame
        features = np.hstack([mfccs, delta_mfccs, delta2_mfccs])  # (n_frames, n_mfcc*3)
        #Logger.log_spimi(features)
        return features
    except Exception as e:
        Logger.log_error(f"Error extracting features from {audio_path}: {e}")
        return None
