from visitor import PrintVisitor, RunVisitor
from scanner import Scanner, Token, TokenType
from column_types import ColumnType
from statement import (
    Statement,
    Program,
    CreateTableStatement,
    DropTableStatement,
    CreateIndexStatement,
    DropIndexStatement,
    CreateColumnDefinition,
    InsertStatement,
    IndexType,
    ConstantExpression,
    IntExpression,
    FloatExpression,
    BoolExpression,
    StringExpression,
    SelectStatement,
    WhereStatement,
)
import time


class Parser:
    def __init__(self, scanner: Scanner, debug: bool = False):
        self.debug = debug
        self.scanner = scanner
        self.prev: Token = None
        self.curr: Token = self.scanner.next_token()

    def print_debug(self, message: str):
        if self.debug:
            print(f"DEBUG: {message} | Current Token: {self.curr}")

    def check(self, token_type: TokenType) -> bool:
        if self.is_at_end():
            return False
        return self.curr.token_type == token_type

    def match(self, token_type: TokenType) -> bool:
        if self.check(token_type):
            self.advance()
            return True
        return False

    def is_at_end(self) -> bool:
        return self.curr.token_type == TokenType.END

    def advance(self) -> bool:
        if not self.is_at_end():
            temp: Token = self.curr
            self.curr = self.scanner.next_token()
            self.prev = temp
            if self.check(TokenType.ERROR):
                raise SyntaxError(f"Syntax error at token: {self.curr.text}")
            return True
        return False

    def parse_column_definition(self) -> CreateColumnDefinition:
        self.print_debug("Parsing column definition")

        column_name, column_type, varchar_length, is_pk = None, None, None, False

        if not self.match(TokenType.USER_IDENTIFIER):
            raise SyntaxError(f"Expected column name, found {self.curr.text}")

        column_name = self.prev.text

        if self.match(TokenType.INT):
            column_type = ColumnType.INT
        elif self.match(TokenType.FLOAT):
            column_type = ColumnType.FLOAT
        elif self.match(TokenType.BOOL):
            column_type = ColumnType.BOOL
        elif self.match(TokenType.DATE):
            column_type = ColumnType.DATE
        elif self.match(TokenType.VARCHAR):
            if not self.match(TokenType.LEFT_PARENTHESIS):
                raise SyntaxError(f"Expected '(' after VARCHAR, found {self.curr.text}")
            if not self.match(TokenType.INT_CONSTANT):
                raise SyntaxError(
                    f"Expected integer constant for VARCHAR length, found {self.curr.text}"
                )
            varchar_length = int(self.prev.text)
            if varchar_length <= 0:
                raise SyntaxError(
                    f"Invalid VARCHAR length {varchar_length}, must be greater than 0"
                )
            if not self.match(TokenType.RIGHT_PARENTHESIS):
                raise SyntaxError(
                    f"Expected ')' after VARCHAR length, found {self.curr.text}"
                )
            column_type = ColumnType.VARCHAR

        if column_type not in (
            ColumnType.INT,
            ColumnType.FLOAT,
            ColumnType.VARCHAR,
            ColumnType.DATE,
            ColumnType.BOOL,
        ):
            raise SyntaxError(
                f"Invalid column type {self.prev.text} for column {column_name}"
            )

        if self.match(TokenType.PRIMARY):
            if not self.match(TokenType.KEY):
                raise SyntaxError(f"Expected KEY after PRIMARY, found {self.curr.text}")
            is_pk = True

        # TODO: allow for index usage in CREATE TABLE

        return CreateColumnDefinition(column_name, column_type, varchar_length, is_pk)

    def parse_column_definition_list(self) -> list[CreateColumnDefinition]:
        self.print_debug("Parsing column definition list")
        columns: list[CreateColumnDefinition] = []

        while not self.check(TokenType.RIGHT_PARENTHESIS):
            columns.append(self.parse_column_definition())
            if self.check(TokenType.COMMA):
                self.advance()

        if len(columns) == 0:
            raise SyntaxError("At least one column definition is required")

        return columns

    # TODO: primary key
    def parse_create_table_statement(self) -> CreateTableStatement:
        self.print_debug("Parsing CREATE TABLE statement")
        table_name = None
        if not self.match(TokenType.USER_IDENTIFIER):
            raise SyntaxError(
                f"Expected table name after CREATE TABLE, found {self.curr.text}"
            )
        table_name = self.prev.text

        if not self.match(TokenType.LEFT_PARENTHESIS):
            raise SyntaxError(f"Expected '(' after table name, found {self.curr.text}")
        columns: list[CreateColumnDefinition] = self.parse_column_definition_list()
        if not self.match(TokenType.RIGHT_PARENTHESIS):
            raise SyntaxError(
                f"Expected ')' after column definitions, found {self.curr.text}"
            )
        return CreateTableStatement(table_name, columns)

    def parse_drop_table_statement(self) -> DropTableStatement:
        self.print_debug("Parsing DROP TABLE statement")
        if not self.match(TokenType.USER_IDENTIFIER):
            raise SyntaxError(
                f"Expected table name after DROP TABLE, found {self.curr.text}"
            )
        table_name = self.prev.text
        return DropTableStatement(table_name)

    def parse_create_index_statement(self) -> CreateIndexStatement:
        self.print_debug("Parsing CREATE INDEX statement")

        # current index implementation doesnt support index name, so we omit it
        # if not self.match(TokenType.USER_IDENTIFIER):
        #     raise SyntaxError(f"Expected index name after CREATE INDEX, found {self.curr.text}")
        # index_name = self.prev.text
        # TODO: change index creation functions to accept and use index name

        if not self.match(TokenType.ON):
            raise SyntaxError(f"Expected ON after index name, found {self.curr.text}")

        if not self.match(TokenType.USER_IDENTIFIER):
            raise SyntaxError(f"Expected table name after ON, found {self.curr.text}")
        table_name = self.prev.text

        if not self.match(TokenType.LEFT_PARENTHESIS):
            raise SyntaxError(f"Expected '(' after table name, found {self.curr.text}")

        if not self.match(TokenType.USER_IDENTIFIER):
            raise SyntaxError(f"Expected column name after '(', found {self.curr.text}")
        column_name = self.prev.text

        if not self.match(TokenType.RIGHT_PARENTHESIS):
            raise SyntaxError(f"Expected ')' after column name, found {self.curr.text}")

        if not self.match(TokenType.USING):
            raise SyntaxError(
                f"Expected USING after column name, found {self.curr.text}"
            )

        if self.match(TokenType.BPLUSTREE):
            index_type = IndexType.BPLUSTREE
        elif self.match(TokenType.EXTENDIBLEHASH):
            index_type = IndexType.EXTENDIBLEHASH
        elif self.match(TokenType.RTREE):
            index_type = IndexType.RTREE
        elif self.match(TokenType.SEQUENTIAL):
            index_type = IndexType.SEQUENTIAL
        else:
            raise SyntaxError(
                f"Expected index type (BPLUSTREE, EXTENDIBLEHASH, RTREE, SEQUENTIAL), found {self.curr.text}"
            )
        return CreateIndexStatement("index_name", table_name, column_name, index_type)

    def parse_drop_index_statement(self) -> DropIndexStatement:
        self.print_debug("Parsing DROP INDEX statement")

        if self.match(TokenType.BPLUSTREE):
            index_type = IndexType.BPLUSTREE
        elif self.match(TokenType.EXTENDIBLEHASH):
            index_type = IndexType.EXTENDIBLEHASH
        elif self.match(TokenType.RTREE):
            index_type = IndexType.RTREE
        elif self.match(TokenType.SEQUENTIAL):
            index_type = IndexType.SEQUENTIAL
        else:
            raise SyntaxError(
                f"Expected index type (BPLUSTREE, EXTENDIBLEHASH, RTREE, SEQUENTIAL), found {self.curr.text}"
            )

        if not self.match(TokenType.ON):
            raise SyntaxError(f"Expected ON after index type, found {self.curr.text}")

        if not self.match(TokenType.USER_IDENTIFIER):
            raise SyntaxError(f"Expected table name after ON, found {self.curr.text}")
        table_name = self.prev.text

        if not self.match(TokenType.LEFT_PARENTHESIS):
            raise SyntaxError(f"Expected '(' after table name, found {self.curr.text}")

        if not self.match(TokenType.USER_IDENTIFIER):
            raise SyntaxError(f"Expected column name after '(', found {self.curr.text}")
        column_name = self.prev.text

        if not self.match(TokenType.RIGHT_PARENTHESIS):
            raise SyntaxError(f"Expected ')' after column name, found {self.curr.text}")

        return DropIndexStatement(index_type, table_name, column_name)

    def parse_insert_statement(self) -> InsertStatement:
        if not self.match(TokenType.INTO):
            raise SyntaxError(f"Expected INTO after INSERT, found {self.curr.text}")

        if not self.match(TokenType.USER_IDENTIFIER):
            raise SyntaxError(f"Expected table name after INTO, found {self.curr.text}")
        table_name = self.prev.text

        if not self.match(TokenType.LEFT_PARENTHESIS):
            raise SyntaxError(f"Expected '(' after table name, found {self.curr.text}")

        columns: list[str] = []
        while not self.check(TokenType.RIGHT_PARENTHESIS):
            if not self.match(TokenType.USER_IDENTIFIER):
                raise SyntaxError(f"Expected column name, found {self.curr.text}")
            columns.append(self.prev.text)

            if self.check(TokenType.COMMA):
                self.advance()
            elif not self.check(TokenType.RIGHT_PARENTHESIS):
                raise SyntaxError(
                    f"Expected ',' or ')' after column name, found {self.curr.text}"
                )

        if not self.match(TokenType.RIGHT_PARENTHESIS):
            raise SyntaxError(
                f"Expected ')' after column names, found {self.curr.text}"
            )

        if not self.match(TokenType.VALUES):
            raise SyntaxError(
                f"Expected VALUES after column names, found {self.curr.text}"
            )

        if not self.match(TokenType.LEFT_PARENTHESIS):
            raise SyntaxError(f"Expected '(' after VALUES, found {self.curr.text}")

        constants: list[ConstantExpression] = []

        while not self.check(TokenType.RIGHT_PARENTHESIS):
            if self.match(TokenType.INT_CONSTANT):
                constants.append(IntExpression(int(self.prev.text)))
            elif self.match(TokenType.FLOAT_CONSTANT):
                constants.append(FloatExpression(float(self.prev.text)))
            elif self.match(TokenType.TRUE) or self.match(TokenType.FALSE):
                constants.append(BoolExpression(self.prev.text.lower() == "true"))
            elif self.match(TokenType.STRING_CONSTANT):
                constants.append(StringExpression(self.prev.text.strip('"').strip("'")))
            else:
                raise SyntaxError(
                    f"Expected constant value (INT, FLOAT, BOOL, STRING), found {self.curr.text}"
                )

            if self.check(TokenType.COMMA):
                self.advance()
            elif not self.check(TokenType.RIGHT_PARENTHESIS):
                raise SyntaxError(
                    f"Expected ',' or ')' after constant value, found {self.curr.text}"
                )

        if not self.match(TokenType.RIGHT_PARENTHESIS):
            raise SyntaxError(
                f"Expected ')' after constant values, found {self.curr.text}"
            )

        return InsertStatement(table_name, columns, constants)

    def parse_where_statement(self) -> WhereStatement:
        raise NotImplementedError("WHERE statement parsing is not implemented yet")

    def parse_select_list(self) -> list[str]:
        select_columns: list[str] = []

        while not self.check(TokenType.FROM):
            table_name, column_name = None, None

            if not self.match(TokenType.USER_IDENTIFIER):
                raise SyntaxError(f"Expected column name, found {self.curr.text}")
            column_name = self.prev.text

            if self.match(TokenType.DOT):
                if not self.match(TokenType.USER_IDENTIFIER):
                    raise SyntaxError(
                        f"Expected table name after '.', found {self.curr.text}"
                    )
                table_name = column_name
                column_name = self.prev.text
            select_columns.append(
                f"{f'{table_name}.' if table_name is not None else ''}{column_name}"
            )

            # TODO: handle column aliases

            if self.check(TokenType.COMMA):
                self.advance()
            elif not self.check(TokenType.FROM):
                raise SyntaxError(
                    f"Expected ',' or FROM after column name, found {self.curr.text}"
                )

        if len(select_columns) == 0:
            raise SyntaxError("At least one column must be selected")
        return select_columns

    def parse_select_statement(self) -> Statement:
        select_columns: list[str] = []
        from_table: str = None
        select_all = False
        where_statement: WhereStatement = None
        order_by_column: str = None
        ascending: bool = True
        limit: int = None
        if self.match(TokenType.ASTERISK):
            select_all = True
        elif self.check(TokenType.USER_IDENTIFIER):
            select_columns = self.parse_select_list()

        if not self.match(TokenType.FROM):
            raise SyntaxError(
                f"Expected FROM after selected columns, found {self.curr.text}"
            )

        if not self.match(TokenType.USER_IDENTIFIER):
            raise SyntaxError(f"Expected table name after FROM, found {self.curr.text}")
        from_table = self.prev.text

        # TODO: handle table alias

        if self.match(TokenType.WHERE):
            where_statement = self.parse_where_statement()

        if self.match(TokenType.ORDER):
            if not self.match(TokenType.BY):
                raise SyntaxError(f"Expected BY after ORDER, found {self.curr.text}")
            if not self.match(TokenType.USER_IDENTIFIER):
                raise SyntaxError(
                    f"Expected column name after ORDER BY, found {self.curr.text}"
                )
            order_by_column = self.prev.text
            ascending = True
            if self.match(TokenType.DESC):
                ascending = False

        if self.match(TokenType.LIMIT):
            if not self.match(TokenType.INT_CONSTANT):
                raise SyntaxError(
                    f"Expected integer constant after LIMIT, found {self.curr.text}"
                )
            limit = int(self.prev.text)

        return SelectStatement(
            select_columns,
            from_table,
            select_all,
            where_statement,
            order_by_column,
            ascending,
            limit,
        )

    def parse_update_statement(self) -> Statement:
        raise NotImplementedError("UPDATE statement parsing is not implemented yet")

    def parse_delete_statement(self) -> Statement:
        raise NotImplementedError("DELETE statement parsing is not implemented yet")

    def parse_statement(self) -> Statement:
        if self.match(TokenType.CREATE):
            if self.match(TokenType.TABLE):
                return self.parse_create_table_statement()
            elif self.match(TokenType.INDEX):
                return self.parse_create_index_statement()
            else:
                raise SyntaxError(
                    f"Expected TABLE or INDEX after CREATE, found {self.curr.text}"
                )
        elif self.match(TokenType.DROP):
            if self.match(TokenType.TABLE):
                return self.parse_drop_table_statement()
            elif self.match(TokenType.INDEX):
                return self.parse_drop_index_statement()
            else:
                raise SyntaxError(
                    f"Expected TABLE or INDEX after DROP, found {self.curr.text}"
                )
        elif self.match(TokenType.INSERT):
            return self.parse_insert_statement()
        elif self.match(TokenType.SELECT):
            return self.parse_select_statement()  # Placeholder for SELECT statement
        elif self.match(TokenType.UPDATE):
            return self.parse_update_statement()
        elif self.match(TokenType.DELETE):
            return self.parse_delete_statement()
        else:
            raise SyntaxError(
                f"Expected statement keyword (CREATE, DROP, etc.), found {self.curr.text}"
            )

    def parse_statement_list(self) -> list[Statement]:
        self.print_debug("Parsing statement list")
        statement_list: list[Statement] = []

        if self.is_at_end():
            return statement_list
        statement = self.parse_statement()
        statement_list.append(statement)

        while self.match(TokenType.SEMICOLON) and not self.is_at_end():
            statement = self.parse_statement()
            statement_list.append(statement)
        return statement_list

    def parse_program(self) -> Program:
        try:
            statement_list = self.parse_statement_list()
            return Program(statement_list)
        except Exception as e:
            print(f"Error parsing program: {e}")
            return None


# endregion

if __name__ == "__main__":
    printVisitor = PrintVisitor()
    execVisitor = RunVisitor()

    table_create_insert = [
        "CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(50), age INT);",
        "CREATE INDEX ON users(name) USING BPLUSTREE;",
        "INSERT INTO users(name, age, id) VALUES ('Alice', 30, 1);",
        "INSERT INTO users(name, id, age) VALUES ('Bob', 2, 20);",
        "INSERT INTO users(age, name, id) VALUES (25, 'Charlie', 3);",
        "INSERT INTO users(id, age, name) VALUES (4, 40, 'David');",
    ]

    table_select = [
        "SELECT users.id, users.age, name FROM users;",
    ]

    queries = [table_select]
    instruction_delay = 1  # seconds

    for queryset in queries:
        for query in queryset:
            scanner = Scanner(query)
            scanner.test()
            parser = Parser(scanner, debug=False)
            program = parser.parse_program()
            printVisitor.visit_program(program)
            # execVisitor.visit_program(program)
            time.sleep(instruction_delay)
