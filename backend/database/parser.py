from mo_sql_parsing import parse
import json
from database import create_table, check_table_exists, get_table_schema, insert_record, get_table_path
import pandas as pd
from enum import Enum
from future.schema import SchemaType
from future.primitives import Varchar
from storage.Record import Record
from storage.HeapFile import HeapFile

class DEBUG_ENABLE(Enum):
    NO = 0
    YES = 1

DEBUG_ENABLE = DEBUG_ENABLE.YES
DEFAULT_VARCHAR_LENGTH = 255

def print_debug(message):
    if DEBUG_ENABLE == DEBUG_ENABLE.YES:
        print(message)

    
TableAbstraction = tuple[str, pd.DataFrame | None] # maps alias to name,df
Level = dict[str, TableAbstraction]

class Environment:
    def __init__(self, other:"Environment"= None):
        if other is not None:
            self.levels = other.levels.copy()
            self.current_level = other.current_level
        else:
            self.levels = {}
            self.levels[0] = Level() # maps int to {name, table} dict
            self.current_level = 0

    def __repr__(self):
        return f"Environment(levels={self.levels}, current_level={self.current_level})"
    
    def descend(self):
        self.current_level += 1
        self.levels[self.current_level] = Level()
    
    def ascend(self):
        if self.current_level == 0:
            raise Exception("Cannot ascend from the root level")
        self.current_level -= 1
        self.levels.pop(self.current_level + 1)

class QueryResult:
    def __init__(self, success: bool, data: TableAbstraction, message:str = None):
        self.success = success
        self.data = data
        self.message = message
    
    def __repr__(self):
        return f"QueryReturnType(success={self.success}, data={self.data}, message={self.message})"

environment = Environment()

class Query:
    def __init__(self, tree: dict, level: int):
        self.tree = tree
        self.level = level

    def evaluate(self):
        if "create table" in self.tree:
            first_clause_type = "create table"
        elif "insert" in self.tree:
            first_clause_type = "insert"
        elif "select" in self.tree:
            first_clause_type = "select"
            
        print_debug(f"Root clause type is {first_clause_type}")

        match first_clause_type:
            case "create table":
                return self.evaluate_create_table(self.tree["create table"])
            case "insert":
                return self.evaluate_insert(self.tree)
            case "select":
                return self.evaluate_select(self.tree)
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
    
    def evaluate_select(self, clause) -> QueryResult:
        # first we need to handle from clause
        try:
            self.evaluate_from(clause["from"]) # sets up environment
        except Exception as e:
            raise Exception(f"Failed to evaluate from clause: {e}")
        
        selectionizer: dict[str, list[str]] = {} # perry the platypus??
        for column_select_clause in clause["select"]:
            attribute = column_select_clause["value"]
            identifier, column = attribute.split(".")
            if identifier not in environment.levels[self.level]:
                raise Exception(f"Identifier {identifier} not found in environment at level {self.level}")
            # we already know the tables exist, but we haven't checked columns yet
            schema: SchemaType = get_table_schema(environment.levels[self.level][identifier][0])
            # now we check if column exists (god i wish schema was a dict and not a list of tuples)
            # print_debug(column)
            # print_debug(schema)
            if column not in [col[0] for col in schema]:
                raise Exception(f"Column {column} does not exist in table/aliased {identifier}")
            selectionizer[identifier] = selectionizer.get(identifier, []) + [column]
        
        # which columns to get from which tables in environment level

        if "where" in clause:
            # uoggggggggghhhhhhhhhhhhhhhh
            pass
        aaa = next(iter(selectionizer.items()))
        return self.handle_select(aaa[0], aaa[1]) # rfdcgfsraseasdsa

    def handle_select(self, name: str, columns: list[str]) -> QueryResult:
        print_debug(f"Selecting {columns} from {name}")
        if environment.levels[self.level][name][1] is None: # if table has not been deserialized yet
            og_name = environment.levels[self.level][name][0]
            heap = HeapFile(get_table_path(og_name))
            environment.levels[self.level][name] = (og_name, HeapFile.to_dataframe(heap)) # tuples are immutable
        df: pd.DataFrame = environment.levels[self.level][name][1]
        df = df[columns] if columns else df
        return QueryResult(success=True, data=df, message=f"Selected {columns} from {name} successfully")

    def evaluate_from(self, from_clause):
        # this does not handle nested selects yet
        if not isinstance(from_clause, list):
            from_clause = [from_clause] # wrap in list to handle single table case

        for item in from_clause:
            if isinstance(item, str):
                if not check_table_exists(item):
                    raise Exception(f"Table {item} does not exist")
                environment.levels[self.level][item] = (item, None) # store at level [x] -> name: name
            elif isinstance(item, dict):
                # handles alias
                og_name = item["value"]
                if not check_table_exists(og_name):
                    raise Exception(f"Table {og_name} does not exist")
                alias = item["name"]
                environment.levels[self.level][alias] = (og_name, None) # store at level [x] -> alias: name (to later fetch actual df but keep alias)
            else:
                raise Exception(f"Unknown from clause type: {type(item)}")
    

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

    create_table = "create table student (id int, name varchar(20), age int);"
    create_table_2 = "create table teacher (id int, name varchar(20), age int, subject varchar);"

    insert = "insert into student (id, name, age) values (1, 'John Doe', 20);"
    insert_2 = "insert into teacher (id, name, age, subject) values (1, 'John Doe', 30, 'Mathematics');"

    select_simple = "select student.id, name from student;"
    select_complex = "select student.id, t.id, t.name from student, teacher as t where student.name = t.name;"

    result = parser.parse(select_complex)
    print(result.message)
    print(result.data)

if __name__ == "__main__":
    main()