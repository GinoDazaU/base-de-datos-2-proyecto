import os
import sys
import shutil
import zipfile
import gdown
import pandas as pd

from logger import Logger

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import (
    create_table,
    insert_record,
    insert_record_free,
    drop_table,
    build_acoustic_model,
    build_acoustic_index,
    knn_search,
    knn_search_index,
)
from storage.Record import Record


def download_and_extract_sounds():
    sounds_dir = "backend/database/sounds"
    zip_path = "backend/database/sounds.zip"
    # Extraído el ID del nuevo enlace
    gdrive_url = "https://drive.google.com/uc?id=15gi6Z5FCl56pLrpyQ_CabTGEiyzYe8rk"

    os.makedirs(sounds_dir, exist_ok=True)

    # Contar archivos existentes
    existing_files = [
        f for f in os.listdir(sounds_dir) if os.path.isfile(os.path.join(sounds_dir, f))
    ]
    num_files = len(existing_files)

    if num_files >= 100:
        Logger.log_debug(
            f"Found {num_files} audio files in '{sounds_dir}'. Skipping download.\n"
        )
        return
    else:
        # Eliminar todos los archivos si hay menos de 100
        Logger.log_debug(
            f"Found only {num_files} files. Cleaning directory and downloading new files..."
        )
        for f in existing_files:
            os.remove(os.path.join(sounds_dir, f))

    Logger.log_debug("Downloading audio ZIP from Google Drive...")
    gdown.download(gdrive_url, zip_path, quiet=False)

    Logger.log_debug("Extracting audio files...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(sounds_dir)

    Logger.log_debug("Cleaning up ZIP file...")
    os.remove(zip_path)
    Logger.log_debug("Download and extraction completed.\n")


def read_csv_and_insert_records(csv_path, table_name, schema):
    Logger.log_debug(f"== LEYENDO CSV DESDE {csv_path} ==")
    df = pd.read_csv(csv_path)

    Logger.log_debug(f"\n== INSERTANDO {len(df)} REGISTROS ==")
    for _, row in df.iterrows():
        values = [
            int(row["id"]),
            str(row["title"]),
            str(row["sound_file"]),
            str(row["artist"]),
            str(row["duration"]),
            str(row["genre"]),
            str(row["url"]),
        ]
        rec = Record(schema, values)
        insert_record_free(table_name, rec)


def main():
    table_name = "songs_knn_index"
    field_name = "sound_file"
    schema = [
        ("id", "INT"),
        ("title", "VARCHAR(100)"),
        (field_name, "sound"),
        ("artist", "VARCHAR(100)"),
        ("duration", "VARCHAR(10)"),
        ("genre", "VARCHAR(50)"),
        ("url", "VARCHAR(300)"),
    ]
    primary_key = "id"
    num_clusters = 10
    k = 3

    # download_and_extract_sounds()

    # if os.path.exists(f"backend/database/tables/{table_name}.dat"):
    #     drop_table(table_name)

    # for suffix in [
    #     ".codebook.pkl",
    #     ".histogram.dat",
    #     "acoustic_index.dat",
    #     "acoustic_index.schema.json",
    #     "acoustic_index_norms.dat",
    #     "acoustic_index_norms.schema.json",
    # ]:
    #     path = (
    #         f"backend/database/tables/{table_name}.{field_name}"
    #         if suffix.startswith(".")
    #         else f"backend/database/tables/{suffix}"
    #     )
    #     if os.path.exists(path):
    #         os.remove(path)

    # Logger.log_debug(f"\n== CREANDO TABLA '{table_name}' ==")
    # create_table(table_name, schema, primary_key)

    # csv_path = "backend/database/testing/canciones_dataset.csv"
    # read_csv_and_insert_records(csv_path, table_name, schema)

    # Logger.log_debug(f"\n== MODELO ACÚSTICO ==")
    # build_acoustic_model(table_name, field_name, num_clusters)
    # Logger.log_debug("Acoustic model built.")

    # Logger.log_debug(f"\n== ÍNDICE ACÚSTICO ==")
    # build_acoustic_index(table_name, field_name)
    # Logger.log_debug("Acoustic index built.")

    query_audio_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "sounds", "000207.mp3")
    )

    Logger.log_debug("\n--- Sequential Search ---")
    results_seq = knn_search(table_name, field_name, query_audio_path, k)
    for record, similarity in results_seq:
        Logger.log_debug(f"  - Record: {record}, Similarity: {similarity:.4f}")

    Logger.log_debug("\n--- Index Search ---")
    results_idx = knn_search_index(table_name, field_name, query_audio_path, k)
    for record, similarity in results_idx:
        Logger.log_debug(f"  - Record: {record}, Similarity: {similarity:.4f}")

    results_seq_gt_0 = {r[0].values[0] for r in results_seq if r[1] > 0}
    results_idx_gt_0 = {r[0].values[0] for r in results_idx if r[1] > 0}

    if (
        results_seq_gt_0 == results_idx_gt_0
        and len(results_seq) == k
        and len(results_idx) == k
    ):
        Logger.log_info("\nTest PASSED! Search results are consistent.")
    else:
        Logger.log_info("\nTest FAILED! Search results are inconsistent.")
        Logger.log_info(f"Sequential (>0): {sorted(list(results_seq_gt_0))}")
        Logger.log_info(f"Index (>0):      {sorted(list(results_idx_gt_0))}")
        Logger.log_info(f"Sequential len: {len(results_seq)}")
        Logger.log_info(f"Index len:      {len(results_idx)}")

    """
    drop_table(table_name)
    for suffix in [
        ".codebook.pkl",
        ".histogram.dat",
        "acoustic_index.dat",
        "acoustic_index.schema.json",
        "acoustic_index_norms.dat",
        "acoustic_index_norms.schema.json",
    ]:
        path = f"backend/database/tables/{table_name}.{field_name}" if suffix.startswith(".") else f"backend/database/tables/{suffix}"
        if os.path.exists(path):
            os.remove(path)
    print(f"Table '{table_name}' dropped and associated files removed.")
    """


if __name__ == "__main__":
    main()
