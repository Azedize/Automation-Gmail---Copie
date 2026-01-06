import logging
import os
import time
from typing import Optional
from queue import Queue
from logging.handlers import QueueHandler, QueueListener


class DevLogger:
    _logger: Optional[logging.Logger] = None
    _listener: Optional[QueueListener] = None
    _queue: Optional[Queue] = None

    @staticmethod
    def init_logger(
        name: str = "DevLogger",
        log_file: str = "logs/dev.log",
        level: int = logging.DEBUG
    ):
        """
        Logger غير حاجز (Async)
        آمن مع Threads و PyQt
        """

        if DevLogger._logger is not None:
            return

        # ================= Queue =================
        log_queue = Queue(-1)  # غير محدودة
        queue_handler = QueueHandler(log_queue)

        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.addHandler(queue_handler)
        logger.propagate = False

        # ================= Formatter =================
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(threadName)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        handlers = []

        # ================= Console =================
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

        # ================= File =================
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

            file_handler = logging.FileHandler(
                log_file,
                mode="a",            # ✅ append (مهم)
                encoding="utf-8"
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            handlers.append(file_handler)

        # ================= Listener =================
        listener = QueueListener(
            log_queue,
            *handlers,
            respect_handler_level=True
        )
        listener.start()

        DevLogger._logger = logger
        DevLogger._listener = listener
        DevLogger._queue = log_queue

        DevLogger.debug("✅ Async Logger initialisé avec succès")

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

    # =========================
    # Arrêt propre (optionnel)
    # =========================

    @staticmethod
    def shutdown():
        if DevLogger._listener:
            DevLogger._listener.stop()
            DevLogger._listener = None
            DevLogger._logger = None
            DevLogger._queue = None





DevLogger = DevLogger()