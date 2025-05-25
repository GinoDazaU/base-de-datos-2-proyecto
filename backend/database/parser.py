from mo_sql_parsing import parse
import json
from database import get_table_path, create_table
from storage.HeapFile import HeapFile
import pandas as pd

class QueryReturnType:
    def __init__(self, success, dataframe: pd.DataFrame = None, error = None):
        self.success = success
        self.data = dataframe
        self.error = error

class Query:
    def __init__(self, query_tree: dict):
        self.query_tree = query_tree

    # select should return the actual data
    # from should return the data from the fetched table

    def evaluate(self):
        root_query_type = next(iter(self.query_tree)) # gets root type of query
        if root_query_type == "select":
            return self.handle_root_select()
        elif root_query_type == "create table":
            return self.handle_root_create_table()

    def handle_root_create_table(self):
        create_clause = self.query_tree["create table"]
        name = create_clause["name"]
        columns_clause = create_clause["columns"] # list of id, type
        schema = []
        for c in columns_clause:
            # column has name and type(has more types)
            col_name = c["name"]
            col_type: dict = c["type"] # pretty type, must convert to fmt for schema
            key = next(iter(col_type))
            if key == "int":
                fmt = "i"
            elif key == "float":
                fmt = "f"
            elif key == "varchar":
                fmt = f"{col_type[key] if len(col_type[key]) > 0 else 255}s" # if just varchar, default to 255
            else:
                raise ValueError(f"Unknown type {key}")
            schema.append((col_name, fmt))

        # create table expects name and schema list[tuple[str, str]]
        try:
            create_table(name, schema)
            return QueryReturnType(True, f"Table {name} created successfully")
        except Exception as e:
            return QueryReturnType(False, pd.DataFrame(), e)

    def handle_root_select(self):
        select_clause = self.query_tree["select"]
        columns_to_select = []
        for item in select_clause:
            if isinstance(item, dict):
                columns_to_select.append(item.get("value"))
            else:
                columns_to_select.append(item)

        from_clause = self.query_tree["from"]
        from_return: QueryReturnType = self.handle_from(from_clause)
        return from_return

    def handle_from(self, from_clause):
        if isinstance(from_clause, str):
            table_path = get_table_path(from_clause)
            heap = HeapFile(table_path)
            HeapFile.to_dataframe(heap)
            return QueryReturnType(True, HeapFile.to_dataframe(heap))
        elif isinstance(from_clause, list):
            # handle recursive from or multiple tables
            pass


    
    def handle_root_create(self):
        return QueryReturnType(True)


class Parser:
    def print_debug(self, message):
        if self.debug:
            print(message)

    def __init__(self, debug = True):
        self.debug = debug

    def parse(self, query: str):
        try:
            parse_tree = parse(query)
            self.print_debug("Parse tree:\n" + json.dumps(parse_tree, indent=2))
            root = Query(parse_tree)
            return root.evaluate()
        except Exception as e:
            self.print_debug(f"Error parsing query: {e}")
            return None
        
    
def main():
    parser = Parser()
    query = "select id, edad from alumno"
    query = "create table test (id int, name varchar)"
    result = parser.parse(query)

if __name__ == "__main__":
    main()