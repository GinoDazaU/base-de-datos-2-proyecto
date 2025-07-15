import librosa
import numpy as np
import matplotlib.pyplot as plt
import os

# Directorios
input_folder = "C:/Users/renat/OneDrive/Documentos/2025/UTEC/2025-I/BDII/base-de-datos-2-proyecto/backend/database/multimedia/fma_small/000"
output_folder = "C:/Users/renat/OneDrive/Documentos/2025/UTEC/2025-I/BDII/base-de-datos-2-proyecto/backend/database/multimedia/features"

# Crear carpeta de salida si no existe
os.makedirs(output_folder, exist_ok=True)

def extract_mfcc(file_path, n_mfcc=13):
    y, sr = librosa.load(file_path, sr=22050)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)  # Shape: (13, n_frames)
    return mfcc

for file_name in os.listdir(input_folder):
    if file_name.endswith(".wav") or file_name.endswith(".mp3"):
        full_path = os.path.join(input_folder, file_name)
        print(f"Procesando: {file_name}")
        mfcc = extract_mfcc(full_path)
        
        # Guardar MFCC como .npy
        base_name = os.path.splitext(file_name)[0]
        output_path = os.path.join(output_folder, base_name + "_mfcc.npy")
        np.save(output_path, mfcc)

print("✅ MFCCs extraídos y guardados.")

mfcc = np.load("C:/Users/renat/OneDrive/Documentos/2025/UTEC/2025-I/BDII/base-de-datos-2-proyecto/backend/database/multimedia/features/000002_mfcc.npy")
plt.imshow(mfcc, aspect='auto', origin='lower')
plt.title("MFCC de Agua Marina - Migajas de Amor")
plt.xlabel("Frame")
plt.ylabel("Coeficiente MFCC")
plt.colorbar()
plt.show()
