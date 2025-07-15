import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from backend.database.storage import Record
from backend.database.storage import HeapFile
import librosa
import numpy as np
import pickle
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics import pairwise_distances_argmin_min

def extract_mfcc_from_audio(audio_path, n_mfcc=13):
    y, sr = librosa.load(audio_path, sr=22050)
    return librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc).T

def load_codebook(path="C:/Users/renat/OneDrive/Documentos/2025/UTEC/2025-I/BDII/base-de-datos-2-proyecto/backend/database/multimedia/codebook.pkl"):
    with open(path, "rb") as f:
        return pickle.load(f)

def vectorize_query(mfcc, codebook, n_clusters=64):
    word_ids, _ = pairwise_distances_argmin_min(mfcc, codebook.cluster_centers_)
    return np.bincount(word_ids, minlength=n_clusters).reshape(1, -1)

def apply_tfidf(query_hist, corpus_tfidf):
    transformer = TfidfTransformer()
    transformer.fit(corpus_tfidf)
    return transformer.transform(query_hist).toarray()

def query_knn(query_vec, corpus, top_k=5):
    similarities = cosine_similarity(query_vec, corpus)[0]
    top_idx = np.argsort(similarities)[::-1][:top_k]
    return [(idx, similarities[idx]) for idx in top_idx]

def fetch_metadata_by_index(idx, heapfile_path="canciones"):
    hf = HeapFile(heapfile_path)
    return hf.fetch_record_by_offset(idx)

def load_tfidf_data(path="C:/Users/renat/OneDrive/Documentos/2025/UTEC/2025-I/BDII/base-de-datos-2-proyecto/backend/database/multimedia/histogramas_TFIDF.pkl"):
    with open(path, "rb") as f:
        return pickle.load(f)

def run_query(audio_path):
    codebook = load_codebook()
    data = load_tfidf_data()
    mfcc = extract_mfcc_from_audio(audio_path)
    hist = vectorize_query(mfcc, codebook, n_clusters=data["codebook_size"])
    query_vec = apply_tfidf(hist, data["tfidf_vectors"])
    results = query_knn(query_vec, data["tfidf_vectors"], top_k=5)
    return [(fetch_metadata_by_index(i), sim) for i, sim in results]
