class Logger:
    info_enabled = False

    def __init__(self, info_enabled: bool):
        self.info_enabled = info_enabled

    @staticmethod
    def log_info(self, message: str):
        if self.info_enabled:
            print(f"[INFO] {message}")
