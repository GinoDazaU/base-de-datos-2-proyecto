import os
import psycopg2
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from psycopg2.extras import execute_values
import pandas as pd
import time
from database import check_table_exists, drop_table, create_table, insert_record, build_spimi_index, search_text, build_acoustic_index
from storage.Record import Record