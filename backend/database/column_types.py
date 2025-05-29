from enum import Enum, auto


class ColumnType(Enum):
    INT = auto()
    FLOAT = auto()
    VARCHAR = auto()
    DATE = auto()
    BOOL = auto()

    def __str__(self):
        return self.name.lower()


class OperationType(Enum):
    EQUAL = auto()  # =
    NOT_EQUAL = auto()  # !=
    GREATER_THAN = auto()  # >
    LESS_THAN = auto()  # <
    GREATER__EQUAL = auto()  # >=
    LESS__EQUAL = auto()  # <=
    IN = auto()  # IN
    BETWEEN = auto()  # BETWEEN

    def __str__(self):
        return self.name.replace("_", " ").lower()


class IndexType(Enum):
    BPLUSTREE = auto()  # int, float, string
    EXTENDIBLEHASH = auto()  # int or string
    RTREE = auto()  # dunno
    SEQUENTIAL = auto()  # int, float, string

    def __str__(self):
        return self.name
