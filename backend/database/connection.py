from statement import (
    CreateTableStatement,
    CreateIndexStatement,
    InsertStatement,
    DropIndexStatement,
    DropTableStatement,
    IntExpression,
    FloatExpression,
    StringExpression,
    BoolExpression,
)
from database import (
    create_table,
    create_seq_idx,
    create_btree_idx,
    create_rtree_idx,
    create_hash_idx,
    check_table_exists,
    drop_table,
    get_table_schema,
    check_seq_idx,
    check_btree_idx,
    check_hash_idx,
    check_rtree_idx,
    drop_seq_idx,
    drop_btree_idx,
    drop_hash_idx,
    drop_rtree_idx,
    insert_record,
)
from fancytypes.schema import SchemaType
from column_types import ColumnType, IndexType
from storage.Record import Record


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
    schema: SchemaType = get_table_schema(st.table_name)  # also checks if table exists
    fmt: str = None

    for name, format in schema:  # WHY IS SCHEMA A LIST
        if st.column_name == name:
            fmt = format
            break

    if fmt is None:
        raise ValueError(
            f"Column '{st.column_name}' does not exist in table '{st.table_name}'."
        )

    actual_type = fmt_to_column_type(fmt)

    if st.index_type == IndexType.BPLUSTREE:
        if actual_type not in (ColumnType.INT, ColumnType.FLOAT, ColumnType.VARCHAR):
            raise ValueError(
                f"B+ Tree index can only be created on INT, FLOAT or VARCHAR columns, not {actual_type}."
            )
        create_btree_idx(st.table_name, st.column_name)
    elif st.index_type == IndexType.EXTENDIBLEHASH:
        if actual_type not in (ColumnType.INT, ColumnType.VARCHAR):
            raise ValueError(
                f"Extendible Hash index can only be created on INT or VARCHAR columns, not {actual_type}."
            )
        create_hash_idx(st.table_name, st.column_name)
    elif st.index_type == IndexType.RTREE:
        raise NotImplementedError("R-Tree index is not implemented yet.")
    elif st.index_type == IndexType.SEQUENTIAL:
        if actual_type not in (ColumnType.INT, ColumnType.FLOAT, ColumnType.VARCHAR):
            raise ValueError(
                f"Sequential index can only be created on INT, FLOAT or VARCHAR columns, not {actual_type}."
            )
        create_seq_idx(st.table_name, st.column_name)
    else:
        raise ValueError(f"Unsupported index type: {st.index_type}")


def DROP_INDEX(st: DropIndexStatement):
    if st.index_type == IndexType.BPLUSTREE:
        if not check_btree_idx(st.table_name, st.column_name):
            raise ValueError(
                f"B+ Tree index on column '{st.column_name}' in table '{st.table_name}' does not exist."
            )
        drop_btree_idx(st.table_name, st.column_name)
    elif st.index_type == IndexType.EXTENDIBLEHASH:
        if not check_hash_idx(st.table_name, st.column_name):
            raise ValueError(
                f"Extendible Hash index on column '{st.column_name}' in table '{st.table_name}' does not exist."
            )
        drop_hash_idx(st.table_name, st.column_name)
    elif st.index_type == IndexType.RTREE:
        if not check_rtree_idx(st.table_name, st.column_name):
            raise ValueError(
                f"R-Tree index on column '{st.column_name}' in table '{st.table_name}' does not exist."
            )
        drop_rtree_idx(st.table_name, st.column_name)
    elif st.index_type == IndexType.SEQUENTIAL:
        if not check_seq_idx(st.table_name, st.column_name):
            raise ValueError(
                f"Sequential index on column '{st.column_name}' in table '{st.table_name}' does not exist."
            )
        drop_seq_idx(st.table_name, st.column_name)
    else:
        raise ValueError(f"Unsupported index type: {st.index_type}")


def INSERT(st: InsertStatement):
    if not check_table_exists(st.table_name):
        raise ValueError(f"Table '{st.table_name}' does not exist.")

    if len(st.column_names) != len(st.values):
        raise ValueError(
            f"Number of column names ({len(st.column_names)}) does not match number of values ({len(st.values)})."
        )

    # now we gotta check thattypes match the table schema
    # we must also follow the order of the column names
    # :(

    schema: SchemaType = get_table_schema(st.table_name)
    schema_dict = {name: fmt for name, fmt in schema}

    for col_name, const_exp in zip(st.column_names, st.values):
        if col_name not in schema_dict:
            raise ValueError(
                f"Column '{col_name}' does not exist in table '{st.table_name}'."
            )

        fmt = schema_dict[col_name]
        actual_type = fmt_to_column_type(fmt)

        if isinstance(const_exp, IntExpression) and actual_type != ColumnType.INT:
            raise ValueError(f"Value for column '{col_name}' must be of type INT.")
        elif isinstance(const_exp, FloatExpression) and actual_type != ColumnType.FLOAT:
            raise ValueError(f"Value for column '{col_name}' must be of type FLOAT.")
        elif (
            isinstance(const_exp, StringExpression)
            and actual_type != ColumnType.VARCHAR
        ):
            raise ValueError(f"Value for column '{col_name}' must be of type VARCHAR.")
        elif isinstance(const_exp, BoolExpression) and actual_type != ColumnType.BOOL:
            raise ValueError(f"Value for column '{col_name}' must be of type BOOL.")

        # else: it's fine, we can insert it
        # but first we check for length of VARCHAR

        if actual_type == ColumnType.VARCHAR:
            if len(const_exp.value) > int(schema_dict[col_name].split("s")[0]):
                raise ValueError(
                    f"Value for column '{col_name}' exceeds maximum length of {schema_dict[col_name].split('s')[0]} characters."
                )
    # all values are valid, but we still need to convert it into a record and give
    # it the values in the right order

    value_dict = dict(zip(st.column_names, st.values), strict=True)
    record_values = []
    for name, fmt in schema:
        if name in value_dict:
            record_values.append(value_dict[name].value)
        else:
            raise ValueError(
                f"Column '{name}' is missing in the insert statement. NULL is not supported yet."
            )
    record = Record(schema, record_values)
    insert_record(st.table_name, record)
