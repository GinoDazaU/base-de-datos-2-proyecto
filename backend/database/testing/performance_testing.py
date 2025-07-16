import os
import psycopg2
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from psycopg2.extras import execute_values
import pandas as pd
import time
from database import check_table_exists, drop_table, create_table, insert_record, build_spimi_index
from storage.Record import Record

class SuppressPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout

csv_path = os.path.join(os.path.dirname(__file__), "news_large.csv")
table_name = "news_text"

def load_to_our_db(df: pd.DataFrame) -> float:
    schema = [
        ("id", "i"),
        ("title", "text")
    ]
    if check_table_exists(table_name):
        drop_table(table_name)
    create_table(table_name, schema, "id")
    start = time.time()
    for _, row in df.iterrows():
        values = [
            int(row["id"]),
            str(row["title"])
        ]
        rec = Record(schema, values)
        insert_record(table_name, rec)
    end = time.time()
    build_spimi_index(table_name)
    return end - start

def load_to_postgres(df: pd.DataFrame) -> float:
    connect = psycopg2.connect(dbname="postgres", user="postgres", password="postgres", host="localhost", port="5432")
    connect.autocommit = True
    postgres = connect.cursor()
    postgres.execute(f"drop table if exists {table_name}")
    postgres.execute(f"""
        create table if not exists {table_name} (
            id integer primary key,
            title text
        )
    """)
    records: list = df.to_records(index=False).tolist()
    start = time.time()
    execute_values(postgres, f"insert into {table_name} (id, title) values %s",
                   records)
    end = time.time()
    return end - start

def test_insertion():
    df = pd.read_csv(csv_path)
    sizes = [10, 1000, 2000, 4000, 8000, 16000, 32000]
    results: list[dict] = []
    for size in sizes[:1]:
        print(f"\nProbando inserción con {size} registros\n")
        subset = df.head(size)
        row = {
            "size": size,
            "our_db": load_to_our_db(subset),
            "postgres": load_to_postgres(subset)
        }
        results.append(row)
    print(pd.DataFrame(results))

test_insertion()