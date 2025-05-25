from mo_sql_parsing import parse
import json
from database import create_table, check_table_exists, get_table_schema, insert_record
from storage.HeapFile import HeapFile
import pandas as pd
from enum import Enum
from future.schema import SchemaType
from future.primitives import Varchar
from storage.Record import Record

class DEBUG_ENABLE(Enum):
    NO = 0
    YES = 1

DEBUG_ENABLE = DEBUG_ENABLE.YES
DEFAULT_VARCHAR_LENGTH = 255

def print_debug(message):
    if DEBUG_ENABLE == DEBUG_ENABLE.YES:
        print(message)

    
TableAbstraction = str | pd.DataFrame | None
Level = dict[str, TableAbstraction]

class Environment:
    def __init__(self, other:"Environment"= None):
        if other is not None:
            self.levels = other.levels.copy()
            self.current_level = other.current_level
        else:
            self.levels = {}
            self.levels[0] = Level()
            self.current_level = 0
    
    def descend(self):
        self.current_level += 1
        self.levels[self.current_level] = Level()
    
    def ascend(self):
        if self.current_level == 0:
            raise Exception("Cannot ascend from the root level")
        self.current_level -= 1
        self.levels.pop(self.current_level + 1)

environment = Environment()

class QueryResult:
    def __init__(self, success: bool, data: TableAbstraction, message:str = None):
        self.success = success
        self.data = data
        self.message = message
    
    def __repr__(self):
        return f"QueryReturnType(success={self.success}, data={self.data}, message={self.message})"

class Query:
    def __init__(self, tree, level: int = 0):
        self.tree = tree
        self.level = level

    def evaluate(self):
        if "create table" in self.tree:
            first_clause_type = "create table"
        elif "insert" in self.tree:
            first_clause_type = "insert"
            
        print_debug(f"Root clause type is {first_clause_type}")

        match first_clause_type:
            case "create table":
                return self.evaluate_create_table(self.tree["create table"])
            case "insert":
                return self.evaluate_insert(self.tree)
            case _:
                raise Exception(f"Unknown root clause type: {first_clause_type}")

        return QueryResult(success=True, message="Query evaluated successfully")
    
    def evaluate_create_table(self, clause) -> QueryResult:
        name = clause["name"]
        if check_table_exists(name):
            raise Exception(f"Table {name} already exists")
        
        columns = clause["columns"]
        schema = SchemaType()

        for column in columns:

            column_name: str = column["name"]
            column_type_left: dict = next(iter(column["type"]))
            column_type:str = ""

            match column_type_left:
                case "int":
                    column_type = "i"
                case "float":
                    column_type = "f"
                case "varchar":
                    column_type_right: dict | int = column["type"][column_type_left]
                    length = column_type_right if isinstance(column_type_right, int) else DEFAULT_VARCHAR_LENGTH
                    column_type = f"{length}s"
            schema.append((column_name, column_type))
        return self.handle_create_table(name, schema)
    
    def handle_create_table(self, name: str, schema: SchemaType) -> QueryResult:
        try:
            create_table(name, schema)
            return QueryResult(success=True, data=None, message=f"Table {name} created successfully")
        except Exception as e:
            raise Exception(f"Failed to create table {name}: {e}")
        
    def evaluate_insert(self, clause) -> QueryResult:
        name = clause["insert"]
        if not check_table_exists(name):
            raise Exception(f"Table {name} does not exist")
        
        schema: SchemaType = get_table_schema(name)

        columns = clause["columns"] # array of strings
        query = clause["query"]["select"]
        values = []

        for query_item, schema_item, column_name in zip(query, schema, columns): # item is a dict with form "value": dict | value
            print_debug(f"Processing query item: {query_item} with schema item: {schema_item} and column name: {column_name}")

            # first, name check
            if column_name != schema_item[0]:
                raise Exception(f"Column name mismatch: {column_name} != {schema_item[0]}")
            
            # then, type check
            FORMAT = schema_item[1]
            value = query_item["value"]
            print_debug(value)
            if isinstance(value, dict): # most likely a string
                literal_value = value["literal"]
                if not isinstance(literal_value, str):
                    raise Exception(f"Expected a string literal for {column_name}, got {literal_value}")
                if not FORMAT.endswith("s"):
                    raise Exception(f"Schema expected {FORMAT}, but got {type(literal_value)}")
                try:
                    to_append = Varchar(literal_value, int(FORMAT[:-1])) # raises exception if varchar exceeds schema varchar size
                except ValueError as _:
                    raise Exception(f"Value for {column_name} exceeds maximum varchar length: {FORMAT[:-1]}")
                values.append(to_append)
            elif isinstance(value, int):
                if FORMAT != "i":
                    raise Exception(f"Schema expected {FORMAT}, but got int")
                values.append(query_item["value"])
            elif isinstance(value, float):
                if FORMAT != "f":
                    raise Exception(f"Schema expected {FORMAT}, but got float")
                values.append(query_item["value"])
        
        print_debug(f"Values to insert: {values}")
        record: Record = Record(schema, values)
        return self.handle_insert(name, record)

    def handle_insert(self, name: str, record:Record) -> QueryResult:
        try:
            insert_record(name, record)
            return QueryResult(success=True, data=None, message=f"Record inserted into table {name} successfully")
        except Exception as e:
            raise Exception(f"Failed to insert record into table {name}: {e}")


class Parser:
    def __init__(self):
        pass

    def parse(self, query: str):
        try:
            tree = parse(query)
            print_debug("Parse tree:\n" + json.dumps(tree, indent=2))
            root = Query(tree, 0)
            return root.evaluate() # should return a QueryResult object
        except Exception as e:
            print_debug(f"Exception at parse(): {e}")
            return QueryResult(success=False, data=None, message=str(e))
        
    
def main():
    parser = Parser()
    query_create_table = "create table student (id int, name varchar(20), age int);"
    insert_query = "insert into student (id, name, age) values (1, 'John Doe', 20);"
    result = parser.parse(insert_query)
    print(result.message)

if __name__ == "__main__":
    main()