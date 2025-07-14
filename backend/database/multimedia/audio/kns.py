import librosa
import numpy as np
import pickle
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.metrics import pairwise_distances_argmin_min

# Parámetros
query_audio_path = ""        
codebook_path = "codebook.pkl"
histogramas_tfidf_path = "histogramas_TFIDF.pkl"
n_clusters = 64
top_k = 5

# Paso 1: Cargar el codebook y los histogramas TF-IDF
with open(codebook_path, "rb") as f:
    kmeans = pickle.load(f)

with open(histogramas_tfidf_path, "rb") as f:
    data = pickle.load(f)
    nombres = data["nombres"]
    tfidf_vectors = data["tfidf_vectors"]

# Paso 2: Procesar el audio de consulta
y, sr = librosa.load(query_audio_path, sr=22050)
mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).T  # (n_frames, 13)

# Asignar cada frame a un acoustic word
word_ids, _ = pairwise_distances_argmin_min(mfcc, kmeans.cluster_centers_)

# Crear histograma de consulta
hist_query = np.bincount(word_ids, minlength=n_clusters).reshape(1, -1)

# Paso 3: Aplicar TF-IDF al vector de consulta
# reusar el mismo TfidfTransformer
tfidf = TfidfTransformer()
tfidf.fit(tfidf_vectors)  # reusar IDF aprendido
query_tfidf = tfidf.transform(hist_query).toarray()

# Paso 4: Calcular similitud coseno
similitudes = cosine_similarity(query_tfidf, tfidf_vectors)[0]

# Paso 5: Obtener Top-K resultados
top_indices = np.argsort(similitudes)[::-1][:top_k]

print("🎧 Canciones más similares:")
for i, idx in enumerate(top_indices):
    print(f"{i+1}. {nombres[idx]} - Similitud: {similitudes[idx]:.4f}")
