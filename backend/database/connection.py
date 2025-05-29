from statement import *
from database import *
from fancytypes.schema import SchemaType
from column_types import ColumnType, IndexType

def fmt_to_column_type(fmt: str) -> ColumnType:
    match fmt:
        case "i":
            return ColumnType.INT
        case "f":
            return ColumnType.FLOAT
        case "?":
            return ColumnType.BOOL
        case _:
            pass
    if fmt.endswith("s"):
        return ColumnType.VARCHAR
    raise ValueError(f"Unsupported format: {fmt}")

def CREATE_TABLE(st: CreateTableStatement):
    if check_table_exists(st.table_name):
        raise ValueError(f"Table '{st.table_name}' already exists.")
    pk: str = None
    schema: SchemaType = []
    for col in st.columns:
        fmt: str = ""
        match col.column_type:
            case ColumnType.INT:
                fmt = "i"
            case ColumnType.FLOAT:
                fmt = "f"
            case ColumnType.VARCHAR:
                fmt = f"{col.varchar_length}s"
            case ColumnType.BOOL:
                fmt = "?"
            case _:
                raise ValueError(f"Unsupported column type: {col.column_type}")
        if col.is_pk:
            if pk is not None:
                raise ValueError("Multiple primary keys are not allowed.")
            pk = col.column_name
        schema.append((col.column_name, fmt))
    
    create_table(st.table_name, schema, pk)

def DROP_TABLE(st: DropTableStatement):
    if not check_table_exists(st.table_name):
        raise ValueError(f"Table '{st.table_name}' does not exist.")
    drop_table(st.table_name)

def CREATE_INDEX(st: CreateIndexStatement):
    schema: SchemaType = get_table_schema(st.table_name) # also checks if table exists
    fmt: str = None

    for name, format in schema: # WHY IS SCHEMA A LIST
        if st.column_name == name:
            fmt = format
            break

    if fmt is None:
        raise ValueError(f"Column '{st.column_name}' does not exist in table '{st.table_name}'.")
    
    actual_type = fmt_to_column_type(fmt)

    if st.index_type == IndexType.BPLUSTREE:
        if actual_type not in (ColumnType.INT, ColumnType.FLOAT, ColumnType.VARCHAR):
            raise ValueError(f"B+ Tree index can only be created on INT, FLOAT or VARCHAR columns, not {actual_type}.")
        create_btree_idx(st.table_name, st.column_name)
    elif st.index_type == IndexType.EXTENDIBLEHASH:
        if actual_type not in (ColumnType.INT, ColumnType.VARCHAR):
            raise ValueError(f"Extendible Hash index can only be created on INT or VARCHAR columns, not {actual_type}.")
        create_hash_idx(st.table_name, st.column_name)
    elif st.index_type == IndexType.RTREE:
        raise NotImplementedError("R-Tree index is not implemented yet.")
    elif st.index_type == IndexType.SEQUENTIAL:
        if actual_type not in (ColumnType.INT, ColumnType.FLOAT, ColumnType.VARCHAR):
            raise ValueError(f"Sequential index can only be created on INT, FLOAT or VARCHAR columns, not {actual_type}.")
        create_seq_idx(st.table_name, st.column_name)
    else:
        raise ValueError(f"Unsupported index type: {st.index_type}")

def DROP_INDEX(st: DropIndexStatement):
    raise NotImplementedError("Drop Index statement is not implemented yet")

def INSERT(st: CreateTableStatement):
    raise NotImplementedError("Insert statement is not implemented yet")




