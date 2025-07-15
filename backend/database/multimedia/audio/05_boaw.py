import os
import numpy as np
import pickle
from sklearn.metrics import pairwise_distances_argmin_min
from sklearn.feature_extraction.text import TfidfTransformer

# Parámetros
features_folder = "C:/Users/renat/OneDrive/Documentos/2025/UTEC/2025-I/BDII/base-de-datos-2-proyecto/backend/database/multimedia/features"
codebook_path = "C:/Users/renat/OneDrive/Documentos/2025/UTEC/2025-I/BDII/base-de-datos-2-proyecto/backend/database/multimedia/codebook.pkl"
n_clusters = 64  # Debe coincidir con el codebook
output_tfidf_path = "C:/Users/renat/OneDrive/Documentos/2025/UTEC/2025-I/BDII/base-de-datos-2-proyecto/backend/database/multimedia/histogramas_TFIDF.pkl"

# Paso 1: Cargar el modelo KMeans (codebook)
with open(codebook_path, "rb") as f:
    kmeans = pickle.load(f)

# Paso 2: Generar histogramas por canción
histogramas = []
nombre_canciones = []

for file in os.listdir(features_folder):
    if file.endswith("_mfcc.npy"):
        path = os.path.join(features_folder, file)
        mfcc = np.load(path).T  # (n_frames, 13)
        
        # Asignar cada frame al cluster más cercano
        word_ids, _ = pairwise_distances_argmin_min(mfcc, kmeans.cluster_centers_)

        # Construir histograma BoAW
        hist = np.bincount(word_ids, minlength=n_clusters)
        histogramas.append(hist)
        
        # Guardar nombre (sin _mfcc.npy)
        nombre = os.path.splitext(file)[0].replace("_mfcc", "")
        nombre_canciones.append(nombre)

# Convertir a matriz (n_canciones x n_clusters)
X = np.array(histogramas)

# Paso 3: Aplicar TF-IDF
tfidf = TfidfTransformer()
X_tfidf = tfidf.fit_transform(X).toarray()

# Paso 4: Guardar resultado
output = {
    "nombres": nombre_canciones,
    "tfidf_vectors": X_tfidf,
    "codebook_size": n_clusters
}

with open(output_tfidf_path, "wb") as f:
    pickle.dump(output, f)

print(f"✅ Histograma TF-IDF guardado en '{output_tfidf_path}' con {len(X_tfidf)} canciones.")
