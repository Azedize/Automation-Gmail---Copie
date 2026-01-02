import logging
import os
import time


class DevLogger:
    _logger = None

    @staticmethod
    def init_logger(
        name: str = "DevLogger",
        log_file: str = "logs/dev.log",
        level=logging.DEBUG
    ):
        if DevLogger._logger is not None:
            return

        logger = logging.getLogger(name)
        logger.setLevel(level)

        # Empêche la duplication des handlers
        if logger.handlers:
            DevLogger._logger = logger
            return

        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # Fichier
        if log_file:
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        DevLogger._logger = logger
        DevLogger.debug("✅ Logger initialisé avec succès")

    # =========================
    # Méthodes de log
    # =========================

    @staticmethod
    def debug(msg: str):
        if DevLogger._logger:
            DevLogger._logger.debug(msg)

    @staticmethod
    def info(msg: str):
        if DevLogger._logger:
            DevLogger._logger.info(msg)

    @staticmethod
    def warning(msg: str):
        if DevLogger._logger:
            DevLogger._logger.warning(msg)

    @staticmethod
    def error(msg: str):
        if DevLogger._logger:
            DevLogger._logger.error(msg)

    @staticmethod
    def critical(msg: str):
        if DevLogger._logger:
            DevLogger._logger.critical(msg)

    @staticmethod
    def exception(msg: str):
        if DevLogger._logger:
            DevLogger._logger.exception(msg)

    # =========================
    # Mesure de temps
    # =========================

    @staticmethod
    def log_time(msg: str, start_time: float):
        elapsed = time.time() - start_time
        DevLogger.info(f"{msg} | Temps écoulé : {elapsed:.3f}s")
        return elapsed




DevLogger = DevLogger()