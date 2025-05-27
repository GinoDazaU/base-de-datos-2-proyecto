from mo_sql_parsing import parse
import json
from database import create_table, check_table_exists, get_table_schema, insert_record, _table_path, insert_record_free, print_table
import pandas as pd
from enum import Enum
from fancytypes.schema import SchemaType
from fancytypes.primitives import Varchar
from storage.Record import Record
from storage.HeapFile import HeapFile
import time
from pprint import pformat

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
    def __init__(self, other: "Environment" = None):
        if other is not None:
            self.levels = {k: v.copy() for k, v in other.levels.items()}
            self.current_level = other.current_level
        else:
            self.inverted_index: dict[int, dict[str, list[str]]] = {} # maps level : column_name, list of aliases to check for ambiguity
            self.inverted_index[0] = {}  # Level 0 is the root level
            self.levels: dict[int, list[TableAbstraction]] = {}
            self.levels[0] = {}  # Level = dict[str, TableAbstraction]
            self.current_level = 0

    def __repr__(self):
        # Print only the table names and aliases, not the full DataFrames
        levels_summary = {
            level: {alias: (name, "DataFrame(...)") for alias, (name, _) in tables.items()}
            for level, tables in self.levels.items()
        }
        return (
            f"Environment(\n"
            f"  current_level={self.current_level},\n"
            f"  levels={pformat(levels_summary, indent=2)},\n"
            f"  inverted_index={pformat(self.inverted_index, indent=2)}\n"
            f")"
        )

    def ensure_level_exists(self, level):
        if level not in self.levels:
            self.levels[level] = {}

    def descend(self):
        self.current_level += 1
        self.ensure_level_exists(self.current_level)
        print_debug(f"Environment descended to level {self.current_level}")


    def ascend(self):
        if self.current_level == 0:
            raise Exception("Cannot ascend from the root level")
        # self.levels.pop(self.current_level) 
        self.current_level -= 1
        print_debug(f"Environment ascended to level {self.current_level}")

class QueryResult:
    """
    Wrapper for query result that adds error checking and status messages.
    """
    def __init__(self, success: bool, data: TableAbstraction, message:str = None):
        self.success = success
        self.data = data
        self.message = message
    
    def __repr__(self):
        return f"QueryReturnType(success={self.success}, data={self.data}, message={self.message})"

environment = Environment()

class Query:
    """
    Query execution unit, can evaluate recursively.

    * "evaluate" functions are entry points for each clause type, they check for valid queries and set up the environment for execution.
    * "handle" functions do most of the work.
    """
    def __init__(self, tree: dict, level: int):
        self.tree = tree
        self.level = level

    def evaluate(self):
        """
        Entry point for query execution.
        """
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
    
    def evaluate_create_table(self, clause) -> QueryResult:
        """
        Checks if table exists, else sets up creation of a table and its schema.
        """
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
        """
        Handles the actual creation of a table.
        """
        try:
            create_table(name, schema, None)
            return QueryResult(success=True, data=None, message=f"Table {name} created successfully")
        except Exception as e:
            raise Exception(f"Failed to create table {name}: {e}")
        
    def evaluate_insert(self, clause) -> QueryResult:
        """
        Does semantic validation, then hands off insertion job to handler function.
        """
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
        """
        Inserts a record into a table.
        """
        try:
            insert_record(name, record)
            return QueryResult(success=True, data=None, message=f"Record inserted into table {name} successfully")
        except Exception as e:
            raise Exception(f"Failed to insert record into table {name}: {e}")
    
    def evaluate_select(self, clause) -> QueryResult:
        if "from" not in clause:
            raise Exception("SELECT clause must have a FROM clause")
        
        try:
            self.evaluate_from(clause["from"]) # builds environment level, sends select clause to check ambiguity
        except Exception as e:
            raise Exception(f"Failed to evaluate from clause: {e}")
        
        # case 1: select * from table
        # case 2: select columns from table (same as above, but list is not empty)
        # case 3: select column, othercolumn from table1, table2 (aliases MUST be unique in level)
        # case 4: select commoncolumn, column from table1, table2 (handle implicit cross join)
        select_clause = clause["select"]

        if not isinstance(select_clause, list):
            select_clause = [select_clause]
        
        columns = []

        for item in select_clause:
            # each item is a dict
            if "all_columns" in item:
                columns = []
                break
            elif "value" in item: # select column_name
                # check for ambiguity in inverted index
                column_name = item["value"]
                table_identifier, col = column_name.split(".") if "." in column_name else (None, column_name)
                print_debug(f"Processing column: {column_name} with alias: {table_identifier} and col: {col}")
                if table_identifier is not None and col not in environment.inverted_index[self.level]: # SELECT table.col FROM table, table2, etc (col doesnt exist anywhere)
                    raise Exception(f"Table {table_identifier} does not have column {col}")
                if col not in environment.inverted_index[self.level]: # SELECT col FROM table1 (table doesnt have col)
                    raise Exception(f"No table has column {col}")
                if len(environment.inverted_index[self.level][col]) > 1 and table_identifier is None: # SELECT col FROM table1, table2, etc (col exists in multiple tables)
                    raise Exception(f"Column {col} is ambiguous, found on tables: {environment.inverted_index[self.level][col]}")
                table_that_has_col = environment.inverted_index[self.level][col][0] # get first table that has the column
                columns.append((table_that_has_col if table_identifier is None else table_identifier) + "." + col) # add table alias if it exists, else just column name
            else:
                raise Exception(f"Unknown select clause item: {item}")

        if "where" in clause:
            self.evaluate_where(clause["where"])
        if "group_by" in clause:
            raise NotImplementedError("GROUP BY clause is not implemented yet")
        if "order_by" in clause:
            raise NotImplementedError("ORDER BY clause is not implemented yet")
        if "limit" in clause:
            raise NotImplementedError("LIMIT clause is not implemented yet")
        
        # handle implicit cross join if more than one table in environment level
        if len(environment.levels[self.level]) > 1 and len(columns) == 0:
            print_debug("Cross join should be done here")
            columns = []

        resulting_table = next(iter(environment.levels[self.level])) # TODO, grabs first table temporarily
        return self.handle_select(resulting_table, columns)
    
    def handle_select(self, name: str, columns: list[str]) -> QueryResult:
        """
        Does the actual selection of columns from a table.
        """
        df: pd.DataFrame = environment.levels[self.level][name][1]
        df = df[columns] if len(columns) > 0 else df # if empty list (*) return full df
        return QueryResult(success=True, data=df, message=f"Selected {columns if len(columns) > 0 else "*"} from {name} successfully")

    def evaluate_from(self, from_clause):
        """
        Builds environment level based on from_clause. Does not handle nested selects yet.
        """
        if not isinstance(from_clause, list):
            from_clause = [from_clause] # wrap in list to handle single table case
                    
        for table in from_clause:
            alias, original_schema_name, df = None, None, None
            if isinstance(table, str): # FROM table_name
                original_schema_name, alias = table, table
                if not check_table_exists(original_schema_name):
                    raise Exception(f"Table {table} does not exist")
            elif isinstance(table, dict): # FROM table_name AS alias
                original_schema_name = table["value"]
                if not check_table_exists(original_schema_name):
                    raise Exception(f"Table {original_schema_name} does not exist")
                alias = table["name"]
            else:
                raise Exception(f"Unknown from clause type: {type(table)}")
            
            hp = HeapFile(_table_path(original_schema_name))
            df = HeapFile.to_dataframe(hp, alias) # dataframes are now built using the (hopefully non ambiguous) alias (if present)

            # columns have table.column format
            for column_name in df.columns:
                _, column_name = column_name.split(".")
                if column_name not in environment.inverted_index[self.level]:
                    environment.inverted_index[self.level][column_name] = []
                environment.inverted_index[self.level][column_name].append(alias) # maps column name to list of aliases at this level
            
            environment.levels[self.level][alias] = (original_schema_name, df) # stores at level [x] -> name/alias: (name, df)

            # when this function returns on evaluate_select, we can check each select clause to check for ambiguity
        print_debug(environment)

    def evaluate_where(self, where_clause):
        """
        Evaluates the WHERE clause.
        """
        if "and" in where_clause:
            raise NotImplementedError("AND operator in WHERE clause is not implemented yet")
        elif "or" in where_clause:
            raise NotImplementedError("OR operator in WHERE clause is not implemented yet")
        else:
            # single comparison
            # format is "op": [val, val]

            mask = self.evaluate_comparison(where_clause)
            print_debug(f"Mask for WHERE clause:\n {mask}")
            alias = next(iter(environment.levels[self.level]))
            original_name = environment.levels[self.level][alias][0] # get the original name of the table
            df = environment.levels[self.level][alias][1] # get the dataframe for the first table in the level
            environment.levels[self.level][alias] = (original_name, df[mask])

    def evaluate_comparison(self, where_clause):
        op = None
        if "eq" in where_clause:
            op = "=="
            left, right = where_clause["eq"]
        elif "gt" in where_clause:
            op = ">"
            left, right = where_clause["gt"]
        elif "lt" in where_clause:
            op = "<"
            left, right = where_clause["lt"]
        elif "gte" in where_clause:
            op = ">="
            left, right = where_clause["gte"]
        elif "lte" in where_clause:
            op = "<="
            left, right = where_clause["lte"]
        elif "neq" in where_clause:
            op = "!="
            left, right = where_clause["neq"]
        else:
            raise Exception(f"Unknown comparison operator: {where_clause}")
        left_value = self.fetch_value(left)
        right_value = self.fetch_value(right)
        print_debug(f"Evaluating comparison: between{type(left_value)} {op} {type(right_value)}")
        return self.handle_comparison(op, left_value, right_value)
    
    def handle_comparison(self, op: str, left_value, right_value):
        if op == '==':
            return left_value == right_value
        elif op == '!=':
            return left_value != right_value
        elif op == '<':
            return left_value < right_value
        elif op == '>':
            return left_value > right_value
        elif op == '<=':
            return left_value <= right_value
        elif op == '>=':
            return left_value >= right_value
        else:
            raise Exception(f"Unsupported operator: {op}")
        
    def fetch_value(self, value):
        if isinstance(value, str): # is a column reference
            return self.resolve_column_reference(value)
        elif isinstance(value, dict): # is a literal value
            literal_value = value["literal"]
            return str(literal_value)
        else:
            return value # int or float

    def resolve_column_reference(self, column_reference: str):
        """
        Resolves a column reference to its value in the current environment.
        """
        table_alias = None
        column_name = None
        if "." not in column_reference:
            # no table alias, just column name
            column_name = column_reference
            if column_name not in environment.inverted_index[self.level]:
                raise Exception(f"Column {column_name} not found at level {self.level}")
            if len(environment.inverted_index[self.level][column_name]) > 1:
                raise Exception(f"Column {column_name} is ambiguous, found on tables: {environment.inverted_index[self.level][column_name]}")
            table_alias = environment.inverted_index[self.level][column_name][0] # get first table that has the column
            df = environment.levels[self.level][table_alias][1]
        else:
            table_alias, column_name = column_reference.split(".")
            if table_alias not in environment.levels[self.level]:
                raise Exception(f"Table alias {table_alias} not found at level {self.level}")
            df = environment.levels[self.level][table_alias][1]

        to_search = table_alias + "." + column_name
        if to_search not in df.columns:
            raise Exception(f"Column {column_name} not found in table {table_alias} at level {self.level}")
        return df[to_search]

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

    create_table = "create table student(id int, name varchar(20), age int);"
    create_table_2 = "create table teacher (id int, name varchar(20), age int, subject varchar);"

    insert = "insert into student(id, name, age) values (1, 'John Doe', 20);"
    insert_2 = "insert into teacher (id, name, age, subject) values (2, 'John Doe', 30, 'Mathematics');"

    select_basic = "select * from student;"
    select_simple = "select student.id, teacher.id from student CROSS JOIN teacher;"
    select_cj = "select * from student, teacher;" # implicit cross join
    select_complex = "select student.id, t.id, t.name, name, * from student, teacher as t"

    insert_error = "insert into student(id, name, age) values(2, 'Pepito', 20)"

    select_error = "select a.id, name, a.age from student as a where id > 1"

    # result = parser.parse(create_table)
    # result = parser.parse(create_table_2)
    # result = parser.parse(insert)
    # result = parser.parse(insert_2)
    for i in range(20):
        insert = f"insert into student(id, name, age) values ({i}, 'John Doe', 20);"
        result = parser.parse(insert)
        print(result.message)
        print(result.data)

def test():
    query = input("Enter a query: ")
    parser = Parser()
    initial_time = time.time()
    result = parser.parse(query)
    print(result.message)
    print(result.data)
    final_time = time.time()
    print(f"Query executed in {(final_time - initial_time) * 1000:.2f} ms")

def wheretest():
    query = "select * from student as a where a.id = 5;"
    parser = Parser()
    initial_time = time.time()
    result = parser.parse(query)
    print(result.message)
    print(result.data)
    final_time = time.time()
    print(f"Query executed in {(final_time - initial_time) * 1000:.2f} ms")

if __name__ == "__main__":
    wheretest()