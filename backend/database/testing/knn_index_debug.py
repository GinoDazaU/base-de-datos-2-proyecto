import os
import sys
import shutil
import zipfile
import gdown

# Add the parent directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import (
    create_table,
    insert_record,
    drop_table,
    build_acoustic_model,
    build_acoustic_index,
    knn_search,
    knn_search_index,
)
from storage.Record import Record
from global_utils import Utils

def download_and_extract_sounds():
    sounds_dir = Utils.build_path("sounds")
    zip_path = Utils.build_path("sounds","sounds.zip")
    gdrive_url = "https://drive.google.com/uc?id=11ZXg2TcG2TOaRFluhJDcojSwlp7MmOCr"

    # Create directory if it doesn't exist
    os.makedirs(sounds_dir, exist_ok=True)

    # Count number of files in the sounds directory
    num_files = len(
        [
            f
            for f in os.listdir(sounds_dir)
            if os.path.isfile(os.path.join(sounds_dir, f))
        ]
    )

    if num_files > 5:
        print(f"Found {num_files} audio files in '{sounds_dir}'. Skipping download.\n")
        return

    print("Downloading audio ZIP from Google Drive...")
    gdown.download(gdrive_url, zip_path, quiet=False)

    print("Extracting audio files...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(sounds_dir)

    print("Cleaning up ZIP file...")
    os.remove(zip_path)
    print("Download and extraction completed.\n")


def main():
    table_name = "songs_knn_index"
    field_name = "sound_file"
    schema = [
        ("id", "int"),
        ("title", "varchar(100)"),
        (field_name, "sound"),
        ("artist", "varchar(100)"),
        ("duration", "varchar(10)"),
        ("genre", "varchar(50)"),
        ("url", "varchar(300)"),
    ]
    primary_key = "id"
    num_clusters = 3
    k = 3

    download_and_extract_sounds()
    # Clean up previous runs
    if os.path.exists(Utils.build_path("tables",f"{table_name}.dat")):
        drop_table(table_name)
    for suffix in [
        ".codebook.pkl",
        ".histogram.dat",
        "acoustic_index.dat",
        "acoustic_index.schema.json",
        "acoustic_index_norms.dat",
        "acoustic_index_norms.schema.json",
    ]:
        path = (
            Utils.build_path("tables",f"{table_name}.{field_name}")
            if suffix.startswith(".")
            else Utils.build_path("tables",f"{suffix}")
        )
        if os.path.exists(path):
            os.remove(path)

    # 1. Create table
    create_table(table_name, schema, primary_key)
    print(f"Table '{table_name}' created.")

    # 2. Insert records
    records_to_insert = [
        (
            1,
            "Food",
            "000002.mp3",
            "AWOL",
            "02:48",
            "Hip-Hop",
            "http://freemusicarchive.org/music/AWOL/AWOL_-_A_Way_Of_Life/Food",
        ),
        (
            2,
            "This World",
            "000005.mp3",
            "AWOL",
            "03:26",
            "Hip-Hop",
            "http://freemusicarchive.org/music/AWOL/AWOL_-_A_Way_Of_Life/This_World",
        ),
        (
            3,
            "Freeway",
            "000010.mp3",
            "Kurt Vile",
            "02:41",
            "Pop",
            "http://freemusicarchive.org/music/Kurt_Vile/Constant_Hitmaker/Freeway",
        ),
        (
            4,
            "Queen Of The Wires",
            "000140.mp3",
            "Alec K. Redfearn & the Eyesores",
            "04:13",
            "Folk",
            "http://freemusicarchive.org/music/Alec_K_Redfearn_and_the_Eyesores/The_Blind_Spot/Queen_Of_The_Wires",
        ),
        (
            5,
            "Ohio",
            "000141.mp3",
            "Alec K. Redfearn & the Eyesores",
            "03:02",
            "Folk",
            "http://freemusicarchive.org/music/Alec_K_Redfearn_and_the_Eyesores/Every_Man_For_Himself/Ohio",
        ),
        (
            6,
            "Blackout 2",
            "000148.mp3",
            "Contradiction",
            "02:18",
            "Avant-Garde",
            "http://freemusicarchive.org/music/Contradiction/Contradiction/Blackout_2",
        ),
    ]

    for r in records_to_insert:
        record = Record(schema, r)
        insert_record(table_name, record)
    print(f"{len(records_to_insert)} records inserted.")

    # 3. Build acoustic model
    build_acoustic_model(table_name, field_name, num_clusters)
    print("Acoustic model built.")

    # 4. Build acoustic index
    build_acoustic_index(table_name, field_name)
    print("Acoustic index built.")

    # 5. Perform k-NN search
    query_audio = "000207.mp3"

    print("\n--- Sequential Search ---")
    results_seq = knn_search(table_name, field_name, query_audio, k)
    print(f"Top {k} most similar songs to '{os.path.basename(query_audio)}':")
    for record, similarity in results_seq:
        print(f"  - Record: {record}, Similarity: {similarity:.4f}")

    print("\n--- Index Search ---")
    results_idx = knn_search_index(table_name, field_name, query_audio, k)
    print(f"Top {k} most similar songs to '{os.path.basename(query_audio)}':")
    for record, similarity in results_idx:
        print(f"  - Record: {record}, Similarity: {similarity:.4f}")

    # 6. Compare results
    results_seq_gt_0 = {r[0].values[0] for r in results_seq if r[1] > 0}
    results_idx_gt_0 = {r[0].values[0] for r in results_idx if r[1] > 0}

    if (
        results_seq_gt_0 == results_idx_gt_0
        and len(results_seq) == k
        and len(results_idx) == k
    ):
        print("\nTest PASSED! Search results are consistent.")
    else:
        print("\nTest FAILED! Search results are inconsistent.")
        print(f"Sequential (>0): {sorted(list(results_seq_gt_0))}")
        print(f"Index (>0):      {sorted(list(results_idx_gt_0))}")
        print(f"Sequential len: {len(results_seq)}")
        print(f"Index len:      {len(results_idx)}")

    # 7. Clean up
    drop_table(table_name)
    for suffix in [
        ".codebook.pkl",
        ".histogram.dat",
        "acoustic_index.dat",
        "acoustic_index.schema.json",
        "acoustic_index_norms.dat",
        "acoustic_index_norms.schema.json",
    ]:
        path = (
            Utils.build_path("tables",f"{table_name}.{field_name}")
            if suffix.startswith(".")
            else Utils.build_path("tables",f"{suffix}")
        )
        if os.path.exists(path):
            os.remove(path)
    print(f"Table '{table_name}' dropped and associated files removed.")


if __name__ == "__main__":
    main()
