from contextlib import contextmanager
from column_types import ColumnType

from statement import (
    CreateTableStatement,
    CreateIndexStatement,
    InsertStatement,
    DropIndexStatement,
    DropTableStatement,
    IntExpression,
    FloatExpression,
    StringExpression,
    SelectStatement,
    WhereStatement,
    Program,
)
from connection import (
    CREATE_TABLE,
    CREATE_INDEX,
    INSERT,
    DROP_INDEX,
    DROP_TABLE,
)


class Visitor:
    """Base visitor class with default behavior"""

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        print("GENERIC VISIT CALLED ON ", node.__class__.__name__)
        pass


# region RunVisitor
class RunVisitor:
    """Base visitor class for executing statements"""

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        print("GENERIC VISIT CALLED ON ", node.__class__.__name__)
        pass

    def visit_program(self, program: Program):
        for st in program.statement_list:
            st.accept(self)

    def visit_createtablestatement(self, st: CreateTableStatement):
        CREATE_TABLE(st)

    def visit_droptablestatement(self, st: DropTableStatement):
        DROP_TABLE(st)

    def visit_createindexstatement(self, st: CreateIndexStatement):
        CREATE_INDEX(st)

    def visit_dropindexstatement(self, st: DropIndexStatement):
        DROP_INDEX(st)

    def visit_insertstatement(self, st: InsertStatement):
        INSERT(st)

    def visit_selectstatement(self, st: SelectStatement):
        raise NotImplementedError("Select statements are not implemented in RunVisitor")

    def visit_wherestatement(self, st: WhereStatement):
        raise NotImplementedError("Where statements are not implemented in RunVisitor")


# endregion


# region PrintVisitor


class PrintVisitor(Visitor):
    def __init__(self, indent_size: int = 2):
        self.indent_level = 0
        self.indent_size = indent_size

    @contextmanager
    def indented(self):
        self.indent_level += 1
        try:
            yield
        finally:
            self.indent_level -= 1

    def print_line(self, text: str, end: str = "\n"):
        indent = " " * (self.indent_level * self.indent_size)
        print(f"{indent}{text}", end=end)

    def visit_intexpression(self, expr: IntExpression):
        self.print_line(f"{expr.value}")

    def visit_floatexpression(self, expr: FloatExpression):
        self.print_line(f"{expr.value}")

    def visit_stringexpression(self, expr: StringExpression):
        self.print_line(f"'{expr.value}'")

    def visit_program(self, program: Program):
        for st in program.statement_list:
            st.accept(self)

    def visit_createtablestatement(self, st: CreateTableStatement):
        self.print_line(f"CREATE TABLE {st.table_name}(")
        with self.indented():
            for column in st.columns:
                column_def = f"{column.column_name} {column.column_type} {'PRIMARY KEY' if column.is_pk else ''}"
                if column.column_type == ColumnType.VARCHAR:
                    column_def += f"({column.varchar_length})"
                self.print_line(
                    f"{column_def}{',' if column != st.columns[-1] else ''}"
                )
        self.print_line(");")

    def visit_droptablestatement(self, statement: DropTableStatement):
        self.print_line(f"DROP TABLE {statement.table_name}")

    def visit_createindexstatement(self, st: CreateIndexStatement):
        self.print_line(
            f"CREATE INDEX ON {st.table_name}({st.column_name}) USING {st.index_type};"
        )

    def visit_dropindexstatement(self, st: DropIndexStatement):
        self.print_line(
            f"DROP INDEX {st.index_type} ON {st.table_name}({st.column_name});"
        )

    def visit_insertstatement(self, st: InsertStatement):
        self.print_line(f"INSERT INTO {st.table_name} VALUES (")
        with self.indented():
            for value in st.values:
                value.accept(self)  # intexpression, floatexpression, stringexpression
                self.print_line(f"{',' if value != st.values[-1] else ''}")
        self.print_line(");")

    def visit_selectstatement(self, st: SelectStatement):
        self.print_line(
            f"SELECT {', '.join(st.select_columns)} FROM {st.from_table}", ""
        )
        if st.where_statement:
            self.print_line("WHERE")
            with self.indented():
                st.where_statement.accept(self)
        self.print_line(";")

    def visit_wherestatement(self, st: WhereStatement):
        self.print_line(
            f"{st.left_expression.accept(self)} {st.operator} {st.right_expression.accept(self)}"
        )


# endregion
