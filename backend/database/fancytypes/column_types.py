from enum import Enum, auto
from tabulate import tabulate


class ColumnType(Enum):
    INT = auto()
    FLOAT = auto()
    VARCHAR = auto()
    DATE = auto()
    BOOL = auto()
    POINT2D = auto()
    POINT3D = auto()
    TEXT = auto()
    SOUND = auto()

    def __str__(self):
        return self.name


class OperationType(Enum):
    EQUAL = auto()  # =
    NOT_EQUAL = auto()  # !=
    GREATER_THAN = auto()  # >
    LESS_THAN = auto()  # <
    GREATER__EQUAL = auto()  # >=
    LESS__EQUAL = auto()  # <=
    IN = auto()  # IN
    BETWEEN = auto()  # BETWEEN
    ATAT = auto()  # @@ for text search
    DISTANCE = auto()  # <-> for distance search

    def __str__(self):
        match self:
            case OperationType.EQUAL:
                return "="
            case OperationType.NOT_EQUAL:
                return "!="
            case OperationType.GREATER_THAN:
                return ">"
            case OperationType.LESS_THAN:
                return "<"
            case OperationType.GREATER__EQUAL:
                return ">="
            case OperationType.LESS__EQUAL:
                return "<="
            case OperationType.IN:
                return "IN"
            case OperationType.BETWEEN:
                return "BETWEEN"
            case OperationType.ATAT:
                return "@@"
            case OperationType.DISTANCE:
                return "<->"
            case _:
                raise ValueError(f"Unknown operation type: {self.name}")


class IndexType(Enum):
    BPLUSTREE = auto()  # int, float, string
    EXTENDIBLEHASH = auto()  # int or string
    RTREE = auto()  # dunno
    SEQUENTIAL = auto()  # int, float, string
    SPIMI = auto()
    SPIMIAUDIO = auto()

    def __str__(self):
        return self.name


class QueryResult:
    def __init__(self, success: bool, message: str = "", data=None):
        self.success = success
        self.message = message
        self.data = data

    def __repr__(self):
        if self.data is None:
            return f"QueryResult(success = {self.success},{' ' if self.success else ''} message = {self.message})"
        data = tabulate(self.data, headers="keys", tablefmt="psql")
        return f"QueryResult(success = {self.success},{' ' if self.success else ''} message = {self.message})\n{data}"
