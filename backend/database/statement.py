from column_types import ColumnType, IndexType
from scanner import TokenType


class Visitable:
    """Base class for all SQL statements"""

    def accept(self, visitor):
        method_name = f"visit_{self.__class__.__name__.lower()}"
        method = getattr(visitor, method_name, visitor.generic_visit)
        return method(self)


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


# endregion


class Program(Visitable):
    def __init__(self, statement_list: list[Statement]):
        self.statement_list = statement_list
