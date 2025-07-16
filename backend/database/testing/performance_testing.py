import os
import psycopg2
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from psycopg2.extras import execute_values
import pandas as pd
import time
from database import check_table_exists, drop_table, create_table, insert_record, build_spimi_index, search_text
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

def load_to_db(df: pd.DataFrame) -> float:
    schema = [
        ("id", "i"),
        ("title", "text")
    ]
    if check_table_exists(table_name):
        drop_table(table_name)
    create_table(table_name, schema, "id")
    start = time.time()
    for _, row in df.iterrows():
        values = [int(row["id"]), str(row["title"])]
        rec = Record(schema, values)
        insert_record(table_name, rec)
    build_spimi_index(table_name)
    end = time.time()
    return end - start

def load_to_pg(df: pd.DataFrame) -> float:
    connect = psycopg2.connect(dbname="postgres", user="postgres", password="postgres", host="localhost", port="5432")
    connect.autocommit = True
    postgres = connect.cursor()
    postgres.execute(f"drop table if exists {table_name}")
    postgres.execute(f"""
        create table if not exists {table_name} (
            id integer primary key,
            title text,
            title_tsv tsvector
        )
    """)
    records: list = df.to_records(index=False).tolist()
    start = time.time()
    execute_values(postgres, f"insert into {table_name} (id, title) values %s",
                   records)
    postgres.execute(f"""
        update {table_name} set title_tsv = to_tsvector('english', title)
    """)
    postgres.execute(f"""
        create index if not exists idx_{table_name}_title_tsv on {table_name} using gin(title_tsv)
    """)
    end = time.time()
    return end - start

def search_db(query: str, k: int) -> tuple[float, list[str]]:
    start = time.time()
    results = search_text(table_name, query, k)
    end = time.time()
    titles = [record.values[1] for record, _ in results]
    return end - start, titles

def search_pg(query: str, k: int) -> tuple[float, list[str]]:
    connect = psycopg2.connect(dbname="postgres", user="postgres", password="postgres", host="localhost", port="5432")
    connect.autocommit = True
    postgres = connect.cursor()
    start = time.time()
    postgres.execute(f"""
        select title from {table_name}
        order by ts_rank(title_tsv, plainto_tsquery('english', %s)) desc
        limit %s
    """, (query, k))
    results = postgres.fetchall()
    end = time.time()
    titles = [result[0] for result in results]
    return end - start, titles

def test_performance():
    df = pd.read_csv(csv_path)
    sizes = [10, 100, 1000, 2000, 4000, 8000, 16000, 32000]
    times: list[dict] = []
    for size in sizes:  
        print(f"\nTrying insertion with {size} records...\n")
        subset = df.head(size)
        row = {
            "size": size,
            "creation_db": load_to_db(subset),
            "creation_pg": load_to_pg(subset),
            "search_db": 0.0,
            "search_pg": 0.0
        }
        db_time, db_titles = search_db("trump obama republican politics", 5)
        pg_time, pg_titles = search_pg("trump obama republican politics", 5)
        row["search_db"] = db_time
        row["search_pg"] = pg_time
        times.append(row)
        print(f"Search results with {size} records:\nOur DB:")
        for title in db_titles:
            print(f"- {title}")
        print(f"\nPostgreSQL:")
        for title in pg_titles:
            print(f"- {title}")
        if db_time > 4*60*60:  # 4 hours
            print(f"Search took too long with {size} records, stopping test.")
            break
    print("\nTime results (s):\n", pd.DataFrame(times))

test_performance()