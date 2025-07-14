import os
import numpy as np
import pickle
from sklearn.cluster import MiniBatchKMeans

# Parámetros
features_folder = "features"
n_clusters = 64  # Número de acoustic words, ajustable según dataset
codebook_path = "codebook.pkl"

# Paso 1: Cargar todos los MFCCs
all_descriptors = []

for file in os.listdir(features_folder):
    if file.endswith("_mfcc.npy"):
        mfcc = np.load(os.path.join(features_folder, file))  # Shape (13, n_frames)
        mfcc = mfcc.T  # Convertimos a (n_frames, 13)
        all_descriptors.append(mfcc)

# Paso 2: Apilar todos los frames de todas las canciones
data = np.vstack(all_descriptors)  # Shape: (total_frames, 13)
print(f"Total de vectores MFCC: {data.shape}")

# Paso 3: Entrenar el KMeans
print("Entrenando KMeans...")
kmeans = MiniBatchKMeans(n_clusters=n_clusters, batch_size=1000, n_init=10)
kmeans.fit(data)

# Paso 4: Guardar el modelo (el codebook acústico)
with open(codebook_path, "wb") as f:
    pickle.dump(kmeans, f)

print(f"✅ Codebook guardado en '{codebook_path}' con {n_clusters} acoustic words.")

from sklearn.metrics import pairwise_distances_argmin_min
import numpy as np
import pickle

# Cargar un MFCC cualquiera
mfcc = np.load("features/000002_mfcc.npy").T

# Cargar el modelo KMeans
with open("codebook.pkl", "rb") as f:
    kmeans = pickle.load(f)

# Asignar cada frame a su acoustic word
words, _ = pairwise_distances_argmin_min(mfcc, kmeans.cluster_centers_)
print(words[:10])  # Ejemplo de primeras asignaciones
