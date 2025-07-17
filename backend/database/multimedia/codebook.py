import numpy as np
import pickle
from sklearn.cluster import KMeans
from storage.HeapFile import HeapFile
from multimedia.feature_extraction import extract_features
from storage.Sound import Sound
import sys
import os
from global_utils import Utils
from logger import Logger

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def build_codebook(heap_file: HeapFile, field_name: str, num_clusters: int):
    """
    Construye un codebook a partir de las características de audio de una tabla.

    Args:
        heap_file (HeapFile): Instancia de HeapFile de la tabla.
        field_name (str): Nombre del campo de tipo SOUND.
        num_clusters (int): Número de clusters para K-Means.
    """
    all_features = []  # Lista para almacenar todos los descriptores (de todos los archivos)
    features_per_file = []  # Guardar descriptores por archivo para calcular doc_freq
    sound_handler = Sound(f"{heap_file.table_name}", field_name)

    for record in heap_file.get_all_records():
        sound_offset, _ = record.values[heap_file.schema.index((field_name, "sound"))]
        audio_path = sound_handler.read(sound_offset)
        features = extract_features(audio_path)  # Matriz (n_frames, n_features)
        if features is not None and len(features) > 0:
            all_features.append(features)
            features_per_file.append(features)

    if not all_features:
        Logger.log_error("No features extracted, cannot build codebook.")
        return

    # Concatenar todos los descriptores en una matriz 2D (n_total_descriptors, n_features)
    all_features_concat = np.vstack(all_features)

    # Entrenar KMeans con todos los descriptores
    kmeans = KMeans(n_clusters=num_clusters, random_state=0, n_init=10).fit(
        all_features_concat
    )

    # Crear el codebook con centroides y frecuencia de documentos
    codebook = {
        "centroids": kmeans.cluster_centers_,
        "doc_freq": np.zeros(num_clusters),
    }

    # Calcular la frecuencia de documentos (cuántos archivos tienen al menos un descriptor asignado a cada cluster)
    for features in features_per_file:
        labels = kmeans.predict(features)  # Asigna cluster para cada descriptor local del archivo
        unique_labels = np.unique(labels)  # Clusters presentes en el archivo
        for label in unique_labels:
            codebook["doc_freq"][label] += 1

    # Guardar el codebook
    codebook_path = Utils.build_path(
        "tables", f"{heap_file.table_name}.{field_name}.codebook.pkl"
    )
    with open(codebook_path, "wb") as f:
        pickle.dump(codebook, f)

    Logger.log_debug(f"Codebook created and saved to {codebook_path}")


