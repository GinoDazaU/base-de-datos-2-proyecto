import pickle
from collections import defaultdict

# Cargar histogramas TF (no TF-IDF)
with open("C:/Users/renat/OneDrive/Documentos/2025/UTEC/2025-I/BDII/base-de-datos-2-proyecto/backend/database/multimedia/histogramas_TFIDF.pkl", "rb") as f:
    data = pickle.load(f)

nombres = data["nombres"]
tfidf_vectors = data["tfidf_vectors"]
n_clusters = data["codebook_size"]

# Convertir TF-IDF de vuelta a TF (aproximadamente)
# O guarda los histogramas TF sin ponderar por separado
X = (tfidf_vectors > 0).astype(int)  # binario como fallback

# Crear índice invertido
inverted_index = defaultdict(dict)

for song_id, vector in enumerate(X):
    for word_id, freq in enumerate(vector):
        if freq > 0:
            inverted_index[word_id][song_id] = freq

# Guardar índice invertido
with open("C:/Users/renat/OneDrive/Documentos/2025/UTEC/2025-I/BDII/base-de-datos-2-proyecto/backend/database/multimedia/inverted_index.pkl", "wb") as f:
    pickle.dump(dict(inverted_index), f)

print(f"✅ Índice invertido creado con {len(inverted_index)} acoustic words.")

import librosa
import numpy as np
import pickle
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import pairwise_distances_argmin_min

#query

query_audio_path = "C:/Users/renat/OneDrive/Documentos/2025/UTEC/2025-I/BDII/base-de-datos-2-proyecto/backend/database/multimedia/fma_small/000/000207.mp3"
top_k = 5

# Cargar recursos
with open("C:/Users/renat/OneDrive/Documentos/2025/UTEC/2025-I/BDII/base-de-datos-2-proyecto/backend/database/multimedia/codebook.pkl", "rb") as f:
    kmeans = pickle.load(f)

with open("C:/Users/renat/OneDrive/Documentos/2025/UTEC/2025-I/BDII/base-de-datos-2-proyecto/backend/database/multimedia/histogramas_TFIDF.pkl", "rb") as f:
    data = pickle.load(f)
    nombres = data["nombres"]
    tfidf_vectors = data["tfidf_vectors"]
    n_clusters = data["codebook_size"]

with open("C:/Users/renat/OneDrive/Documentos/2025/UTEC/2025-I/BDII/base-de-datos-2-proyecto/backend/database/multimedia/inverted_index.pkl", "rb") as f:
    inverted_index = pickle.load(f)

# Procesar query
y, sr = librosa.load(query_audio_path, sr=22050)
mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13).T
word_ids, _ = pairwise_distances_argmin_min(mfcc, kmeans.cluster_centers_)
hist_query = np.bincount(word_ids, minlength=n_clusters).reshape(1, -1)

# TF-IDF para el query
tfidf = TfidfTransformer()
tfidf.fit(tfidf_vectors)
query_tfidf = tfidf.transform(hist_query).toarray()[0]

# Recuperar candidatos desde el índice invertido
candidatos = set()
for word_id in np.nonzero(hist_query[0])[0]:
    if word_id in inverted_index:
        candidatos.update(inverted_index[word_id].keys())

# Calcular similitud solo con los candidatos
resultados = []
for idx in candidatos:
    sim = cosine_similarity([query_tfidf], [tfidf_vectors[idx]])[0][0]
    resultados.append((sim, idx))

# Ordenar y mostrar
top_resultados = sorted(resultados, reverse=True)[:top_k]

print("🎯 Resultados (índice invertido):")
for rank, (sim, idx) in enumerate(top_resultados, 1):
    print(f"{rank}. {nombres[idx]} - Similitud: {sim:.4f}")
