class Logger:
    info_enabled = False
    error_enabled = False
    dbmanager_enabled = False
    debug_enabled = False

    def __init__(
        self,
        info_enabled: bool = False,
        error_enabled: bool = False,
        dbmanager_enabled: bool = False,
        debug_enabled: bool = False,
    ):
        self.info_enabled = info_enabled
        self.error_enabled = error_enabled
        self.dbmanager_enabled = dbmanager_enabled
        self.debug_enabled = debug_enabled

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
    @classmethod
    def log_info(cls, *args):
        if cls.info_enabled:
            print("[INFO]", *args)
