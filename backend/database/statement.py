from column_types import ColumnType, IndexType, OperationType
from scanner import TokenType


class Visitable:
    """Base class for all SQL statements"""

    def accept(self, visitor):
        method_name = f"visit_{self.__class__.__name__.lower()}"
        method = getattr(visitor, method_name, visitor.generic_visit)
        return method(self)


# region Expression Classes
class ConstantExpression(Visitable):
    def __init__(self):
        pass


class IntExpression(ConstantExpression):
    def __init__(self, value: int):
        self.value = value


class FloatExpression(ConstantExpression):
    def __init__(self, value: float):
        self.value = value


class BoolExpression(ConstantExpression):
    def __init__(self, value: bool):
        self.value = value


class StringExpression(ConstantExpression):
    def __init__(
        self,
        value: str,
    ):
        self.value = value


# endregion


class ColumnExpression(Visitable):
    def __init__(self, column_name: str, table_name: str = None):
        self.column_name = column_name
        self.table_name = table_name

    def __str__(self):
        if self.table_name:
            return f"{self.table_name}.{self.column_name}"
        return self.column_name


# region Statement Classes
class Statement(Visitable):
    def __init__(self):
        pass


class CreateColumnDefinition:
    def __init__(
        self,
        column_name=None,
        column_type: ColumnType = None,
        varchar_length: int = None,
        is_pk: bool = False,
    ):
        self.column_name = column_name
        self.column_type = column_type
        self.varchar_length = (
            varchar_length if column_type == ColumnType.VARCHAR else None
        )
        self.is_pk = is_pk


class CreateTableStatement(Statement):
    def __init__(self, table_name: str, columns: list[CreateColumnDefinition]):
        self.table_name = table_name
        self.columns = columns


class DropTableStatement(Statement):
    def __init__(self, table_name: str):
        self.table_name = table_name


class CreateIndexStatement(Statement):
    def __init__(
        self, index_name: str, table_name: str, column_name: str, index_type: IndexType
    ):
        self.index_name = index_name  # not used
        self.table_name = table_name
        self.column_name = column_name
        self.index_type = index_type


class DropIndexStatement(Statement):
    def __init__(self, index_type: IndexType, table_name: str, column_name: str):
        self.index_type = index_type
        self.table_name = table_name
        self.column_name = column_name


class InsertStatement(Statement):
    def __init__(
        self, table_name: str, column_names: list[str], values: list[ConstantExpression]
    ):
        self.table_name = table_name
        self.column_names = column_names
        self.values = values


class WhereStatement(Visitable):
    def __init__(
        self,
        left_expression: Visitable,
        operator: OperationType,
        right_expression: Visitable,
    ):
        self.left_expression = left_expression
        self.operator = operator
        self.right_expression = right_expression


class SelectStatement(Statement):
    def __init__(
        self,
        select_columns: list[str],
        from_table: str,  # for now we only support one table, we can expand it with joins later
        select_all: bool = False,
        where_statement: WhereStatement = None,
        order_by_column: str = None,
        ascending: bool = False,
        limit: int = None,
    ):
        self.select_columns = select_columns
        self.select_all = select_all
        self.from_table = from_table
        self.where_statement = where_statement
        self.order_by_column = order_by_column
        self.ascending = ascending
        self.limit = limit


# endregion


# region Select Statement Stuff


class Program(Visitable):
    def __init__(self, statement_list: list[Statement]):
        self.statement_list = statement_list
