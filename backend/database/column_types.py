from enum import Enum, auto

class ColumnType(Enum):
    INT = auto()
    FLOAT = auto()
    VARCHAR = auto()
    DATE = auto()
    BOOL = auto()

    def __str__(self):
        return self.name.lower()

class IndexType(Enum):
    BPLUSTREE = auto() # int, float, string
    EXTENDIBLEHASH = auto() # int or string
    RTREE = auto() # dunno
    SEQUENTIAL = auto() # int, float, string

    def __str__(self):
        return self.name