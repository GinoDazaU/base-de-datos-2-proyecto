class Logger:
    info_enabled = False
    error_enabled = False
    dbmanager_enabled = False
    debug_enabled = False
    parser_enabled = False
    spimi_enabled = False

    def __init__(
        self,
        info_enabled: bool = False,
        error_enabled: bool = False,
        dbmanager_enabled: bool = False,
        debug_enabled: bool = False,
        parser_enabled: bool = False,
        spimi_enabled: bool = False,
    ):
        self.info_enabled = info_enabled
        self.error_enabled = error_enabled
        self.dbmanager_enabled = dbmanager_enabled
        self.debug_enabled = debug_enabled
        self.parser_enabled = parser_enabled
        self.spimi_enabled = spimi_enabled

    @staticmethod
    def log_info(message: str):
        if Logger.info_enabled:
            print(f"[INFO] {message}")

    @staticmethod
    def log_error(message: str):
        if Logger.error_enabled:
            print(f"[ERROR] {message}")

    @staticmethod
    def log_dbmanager(message: str):
        if Logger.dbmanager_enabled:
            print(f"[DBMANAGER] {message}")

    @staticmethod
    def log_debug(message: str):
        if Logger.debug_enabled:
            print(f"[DEBUG] {message}")

    @staticmethod
    def log_parser(message: str):
        if Logger.parser_enabled:
            print(f"[PARSER] {message}")
    @staticmethod
    def log_spimi(message: str):
        if Logger.spimi_enabled:
            print(f"[SPIMI] {message}")
