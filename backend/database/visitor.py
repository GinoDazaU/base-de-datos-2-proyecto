from contextlib import contextmanager

from fancytypes.column_types import (
    ColumnType,
    QueryResult,
    OperationType,
    IndexType,
)

from dbmanager import DBManager

from statement import (
    AndCondition,
    BetweenComparison,
    ConstantCondition,
    NotCondition,
    OrCondition,
    PrimaryCondition,
    SimpleComparison,
    Statement,
    CreateTableStatement,
    CreateIndexStatement,
    InsertStatement,
    DropIndexStatement,
    DropTableStatement,
    IntExpression,
    FloatExpression,
    StringExpression,
    BoolExpression,
    ColumnExpression,
    SelectStatement,
    WhereStatement,
    KnnStatement,
    TextSearchStatement,
    Program,
    Point2DExpression,
    Point3DExpression,
    Condition,
)

from logger import Logger
import pandas as pd


def fmt_to_column_type(fmt: str) -> ColumnType:
    match fmt:
        case "i":
            return ColumnType.INT
        case "f":
            return ColumnType.FLOAT
        case "?":
            return ColumnType.BOOL
        case "2f":
            return ColumnType.POINT2D
        case "3f":
            return ColumnType.POINT3D
        case "text":
            return ColumnType.TEXT
        case "sound":
            return ColumnType.SOUND
        case _:
            pass  # TODO: implement dates
    if fmt.endswith("s"):
        return ColumnType.VARCHAR
    raise ValueError(f"Unsupported format: {fmt}")


def column_type_to_fmt(column_type: ColumnType, varchar_length: int) -> str:
    match column_type:
        case ColumnType.INT:
            return "i"
        case ColumnType.FLOAT:
            return "f"
        case ColumnType.VARCHAR:
            return f"{varchar_length}s"
        case ColumnType.BOOL:
            return "?"
        case ColumnType.POINT2D:
            return "2f"
        case ColumnType.POINT3D:
            return "3f"
        case ColumnType.TEXT:
            return "text"
        case ColumnType.SOUND:
            return "sound"
        case _:
            raise ValueError(f"Unsupported column type: {column_type}")


class Visitor:
    """Base visitor class with default behavior"""

    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        print("GENERIC VISIT CALLED ON ", node.__class__.__name__)
        pass


# region RunVisitor
class RunVisitor:
    """Base visitor class for executing statements"""

    def __init__(self):
        self.current_table: str = ""
        self.k = 10  # default

    def generic_visit(self, node):
        if isinstance(node, Statement):
            raise ValueError(f"No visit_{node.__class__.__name__.lower()} method defined for {node.__class__.__name__}")
        if isinstance(node, Condition):
            return set()
        raise ValueError(f"No visit_{node.__class__.__name__.lower()} method defined for {node.__class__.__name__}")

    def visit_intexpression(self, expr: IntExpression):
        return expr.value

    def visit_floatexpression(self, expr: FloatExpression):
        return expr.value

    def visit_stringexpression(self, expr: StringExpression):
        return expr.value

    def visit_boolexpression(self, expr: BoolExpression):
        return expr.value

    def visit_point2dexpression(self, expr: Point2DExpression):
        return (expr.x, expr.y)

    def visit_point3dexpression(self, expr: Point3DExpression):
        return (expr.x, expr.y, expr.z)

    def visit_columnexpression(self, expr: ColumnExpression):
        return "§" + self.current_table + "." + expr.column_name

    def visit_program(self, program: Program):
        lastResult: QueryResult = None
        for st in program.statement_list:
            lastResult = st.accept(self)

            Logger.log_info(f"Program parsed successfully with final message: {lastResult.message}")

        return lastResult

    def visit_createtablestatement(self, st: CreateTableStatement):
        table_exists: bool = DBManager.check_table_exists(st.table_name)

        if table_exists:
            if st.if_not_exists:
                return QueryResult(True, f"Table '{st.table_name}' already exists, skipping creation.")
            else:
                return QueryResult(False, f"Table '{st.table_name}' already exists.")

        try:
            DBManager().create_table(st.table_name, st.columns)
            return QueryResult(True, f"Table '{st.table_name}' created successfully.")
        except Exception as e:
            Logger.log_error(str(e))
            return QueryResult(False, f"There was an error while creating the table: {str(e)}")

    def visit_droptablestatement(self, st: DropTableStatement):
        try:
            DBManager().drop_table(st.table_name)
            Logger.log_info(f"Table '{st.table_name}' dropped successfully.")
            return QueryResult(True, f"Table '{st.table_name}' dropped successfully.")
        except Exception as e:
            Logger.log_error(str(e))
            return QueryResult(False, f"There was an error while droppping the table: {str(e)}")

    def visit_createindexstatement(self, st: CreateIndexStatement):
        try:
            DBManager().create_index(st.table_name, st.column_name, st.index_type)
            Logger.log_info(f"{st.index_type} on {st.table_name}.{st.column_name} created successfully.")
            return QueryResult(
                True,
                f"{st.index_type} on {st.table_name}.{st.column_name} created successfully.",
            )
        except Exception as e:
            Logger.log_error(str(e))
            return QueryResult(False, f"There was an error while creating the index: {str(e)}")

    def visit_dropindexstatement(self, st: DropIndexStatement):
        try:
            DBManager().drop_index(st.table_name, st.column_name, st.index_type)
            Logger.log_info(f"{st.index_type} on {st.table_name}.{st.column_name} dropped successfully.")
            return QueryResult(
                True,
                f"{st.index_type} on {st.table_name}.{st.column_name} dropped successfully.",
            )
        except Exception as e:
            Logger.log_error(str(e))
            return QueryResult(False, f"There was an error while dropping the index: {str(e)}")

    def visit_insertstatement(self, st: InsertStatement):
        try:
            values = [exp.accept(self) for exp in st.values]
            DBManager().insert(st.table_name, st.column_names, values)
            Logger.log_info(f"Record inserted into table '{st.table_name}' successfully.")
            return QueryResult(
                True,
                f"Record inserted into table '{st.table_name}' successfully.",
            )
        except Exception as e:
            Logger.log_error(str(e))
            return QueryResult(False, f"There was an error while inserting: {str(e)}")

    def visit_selectstatement(self, st: SelectStatement):
        try:
            if st.limit is not None:
                Logger.log_debug(f"SET K TO {st.limit}")
                self.k = st.limit  # awful
            self.current_table = st.from_table
            offsets: set[int] = (
                DBManager().fetch_all_offsets(st.from_table) if not st.where_statement else st.where_statement.accept(self)
            )
            columns = None if st.select_all else st.select_columns
            results: pd.DataFrame = DBManager().records_projection(st.from_table, offsets, columns, as_df=True)
            Logger.log_debug("PASSED PROJECTION")
            if st.limit is not None:
                results = results[: st.limit]

            Logger.log_info(f"Selected {len(results)} records from table '{st.from_table}'.")
            return QueryResult(
                True,
                f"Selected {len(results)} records from table '{st.from_table}'.",
                results,
            )
        except Exception as e:
            Logger.log_error(str(e))
            return QueryResult(False, f"There was an error while selecting records: {str(e)}")

    # region RunVisitor Conditions

    def visit_wherestatement(self, st: WhereStatement) -> set[int]:
        return st.or_condition.accept(self)

    def visit_knnstatement(self, st: KnnStatement):
        return DBManager().do_audio_knn(st.table_name, st.column_name, st.query_path, st.k)

    def visit_textsearchstatement(self, st: TextSearchStatement):
        return DBManager().do_text_search(st.table_name, st.query_text, st.k)

    def visit_orcondition(self, condition: OrCondition):
        left = condition.and_condition.accept(self)
        if condition.or_condition:
            right = condition.or_condition.accept(self)
            return left | right
        return left

    def visit_andcondition(self, condition: AndCondition):
        left = condition.not_condition.accept(self)
        if condition.and_condition:
            right = condition.and_condition.accept(self)
            return left & right
        return left

    def visit_notcondition(self, condition: NotCondition):
        inner = condition.primary_condition.accept(self)
        return DBManager().fetch_all_offsets(self.current_table) - inner if condition.is_not else inner

    def visit_constantcondition(self, condition: ConstantCondition):
        return DBManager().fetch_all_offsets(self.current_table) if condition.bool_constant.accept(self) else set()

    def visit_simplecomparison(self, condition: SimpleComparison):
        left_value = condition.left_expression.accept(self)
        right_value = condition.right_expression.accept(self)
        return DBManager().fetch_condition_offsets(self.current_table, left_value, condition.operator, right_value, self.k)

    def visit_betweencomparison(self, condition: BetweenComparison):
        left_value = condition.left_expression.accept(self)
        low = condition.lower_bound.accept(self)
        high = condition.upper_bound.accept(self)
        return DBManager().fetch_condition_offsets(self.current_table, left_value, OperationType.BETWEEN, (low, high), self.k)

    def visit_primarycondition(self, condition: PrimaryCondition):
        if isinstance(condition.condition, ConstantCondition):
            return condition.condition.accept(self)
        elif isinstance(condition.condition, SimpleComparison):
            return condition.condition.accept(self)
        elif isinstance(condition.condition, BetweenComparison):
            return condition.condition.accept(self)
        elif isinstance(condition.condition, OrCondition):
            return condition.condition.accept(self)  # nested OrCondition
        else:
            raise ValueError(f"Unsupported condition type: {type(condition.condition)}")

    # endregion


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
        self.print_line(f"{expr.value}", "")

    def visit_floatexpression(self, expr: FloatExpression):
        self.print_line(f"{expr.value}", "")

    def visit_stringexpression(self, expr: StringExpression):
        self.print_line(f"'{expr.value}'", "")

    def visit_boolexpression(self, expr: BoolExpression):
        self.print_line("TRUE" if expr.value else "FALSE", "")

    def visit_point2dexpression(self, expr: Point2DExpression):
        self.print_line(f"POINT2D({expr.x}, {expr.y})", "")

    def visit_point3dexpression(self, expr: Point3DExpression):
        self.print_line(f"POINT3D({expr.x}, {expr.y}, {expr.z})", "")

    def visit_columnexpression(self, expr: ColumnExpression):
        if expr.table_name:
            self.print_line(f"{expr.table_name}.{expr.column_name}", "")
        else:
            self.print_line(expr.column_name, "")

    def visit_program(self, program: Program):
        for st in program.statement_list:
            st.accept(self)

    def visit_createtablestatement(self, st: CreateTableStatement):
        self.print_line(f"CREATE TABLE {'IF NOT EXISTS ' if st.if_not_exists else ''}{st.table_name}(")
        with self.indented():
            for column in st.columns:
                column_def = f"{column.column_name} {column.column_type}{' PRIMARY KEY' if column.is_pk else ''}"
                if column.column_type == ColumnType.VARCHAR:
                    column_def += f"({column.varchar_length})"
                self.print_line(f"{column_def}{',' if column != st.columns[-1] else ''}")
        self.print_line(");")

    def visit_droptablestatement(self, statement: DropTableStatement):
        self.print_line(f"DROP TABLE {statement.table_name}")

    def visit_createindexstatement(self, st: CreateIndexStatement):
        if st.index_type not in [IndexType.SPIMI, IndexType.SPIMIAUDIO]:
            self.print_line(f"CREATE INDEX ON {st.table_name}({st.column_name}) USING {st.index_type};")
        else:
            self.print_line(f"CREATE {str(st.index_type)} ON {st.table_name};")

    def visit_dropindexstatement(self, st: DropIndexStatement):
        self.print_line(f"DROP INDEX {st.index_type} ON {st.table_name}({st.column_name});")

    def visit_insertstatement(self, st: InsertStatement):
        self.print_line(f"INSERT INTO {st.table_name} VALUES(")
        for value in st.values:
            with self.indented():
                value.accept(self)  # intexpression, floatexpression, stringexpression
            self.print_line(f"{',' if value != st.values[-1] else ''}")
        self.print_line(");")

    def visit_selectstatement(self, st: SelectStatement):
        self.print_line(
            f"SELECT {'*' if st.select_all else ', '.join(st.select_columns)} FROM {st.from_table}",
            "",
        )
        if st.where_statement:
            st.where_statement.accept(self)
        if st.limit is not None:
            self.print_line(f" LIMIT {st.limit}", "")
        self.print_line(";")

    def visit_knnstatement(self, st: KnnStatement):
        self.print_line(
            f"KNN({st.k}) SOUND('{st.query_path}') IN {st.table_name}.{st.column_name};",
        )

    def visit_textsearchstatement(self, st: TextSearchStatement):
        self.print_line(
            f"TEXTSEARCH '{st.query_text}' IN {st.table_name};",
        )

    # region PrintVisitor Conditions
    def visit_orcondition(self, condition: OrCondition):
        condition.and_condition.accept(self)
        if condition.or_condition is not None:
            self.print_line(" OR ", "")
            condition.or_condition.accept(self)

    def visit_andcondition(self, condition: AndCondition):
        condition.not_condition.accept(self)
        if condition.and_condition is not None:
            self.print_line(" AND ", "")
            condition.and_condition.accept(self)

    def visit_notcondition(self, condition: NotCondition):
        if condition.is_not:
            self.print_line(" NOT ", "")
        condition.primary_condition.accept(self)

    def visit_constantcondition(self, condition: ConstantCondition):
        condition.bool_constant.accept(self)

    def visit_simplecomparison(self, condition: SimpleComparison):
        condition.left_expression.accept(self)
        self.print_line(f" {condition.operator} ", "")
        condition.right_expression.accept(self)

    def visit_betweencomparison(self, condition: BetweenComparison):
        condition.left_expression.accept(self)
        self.print_line(" BETWEEN ", "")
        condition.lower_bound.accept(self)
        self.print_line(" AND ", "")
        condition.upper_bound.accept(self)

    def visit_primarycondition(self, condition: PrimaryCondition):
        if isinstance(condition.condition, ConstantCondition):
            condition.condition.accept(self)
        elif isinstance(condition.condition, SimpleComparison):
            condition.condition.accept(self)
        elif isinstance(condition.condition, BetweenComparison):
            condition.condition.accept(self)
        elif isinstance(condition.condition, OrCondition):
            self.print_line("(", "")  # cause nested
            condition.condition.accept(self)
            self.print_line(")", "")
        else:
            raise ValueError(f"Unsupported condition type: {type(condition.condition)}")

    # endregion

    def visit_wherestatement(self, st: WhereStatement):
        self.print_line(" WHERE ", "")
        st.or_condition.accept(self)


# endregion
