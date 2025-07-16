class Logger:
    info_enabled = False

    def __init__(self, info_enabled: bool):
        self.info_enabled = info_enabled

    @classmethod
    def log_info(cls, *args):
        if cls.info_enabled:
            print("[INFO]", *args)
