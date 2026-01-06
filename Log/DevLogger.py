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

        print("🟡 [LOGGER] Initialisation du logger...")

        if DevLogger._logger is not None:
            print("⚠️ [LOGGER] Logger déjà initialisé — skip")
            return

        # ================= Queue =================
        print("🟢 [LOGGER] Création de la Queue")
        log_queue = Queue(-1)

        try:
            queue_handler = QueueHandler(log_queue)
            print("✅ [LOGGER] QueueHandler OK")
        except Exception as e:
            print("❌ [LOGGER] Erreur QueueHandler:", e)
            raise

        # ================= Logger =================
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.addHandler(queue_handler)
        logger.propagate = False

        print(f"🧠 [LOGGER] Logger '{name}' configuré")

        # ================= Formatter =================
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(threadName)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        handlers = []

        # ================= Console =================
        try:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            handlers.append(console_handler)
            print("🖥️ [LOGGER] Console handler OK")
        except Exception as e:
            print("❌ [LOGGER] Erreur Console handler:", e)
            raise

        # ================= File =================
        if log_file:
            try:
                log_dir = os.path.dirname(log_file)
                if log_dir:
                    os.makedirs(log_dir, exist_ok=True)
                    print(f"📁 [LOGGER] Dossier log prêt: {log_dir}")

                file_handler = logging.FileHandler(
                    log_file,
                    mode="a",
                    encoding="utf-8"
                )
                file_handler.setLevel(level)
                file_handler.setFormatter(formatter)
                handlers.append(file_handler)
                print(f"📄 [LOGGER] File handler OK: {log_file}")
            except Exception as e:
                print("❌ [LOGGER] Erreur File handler:", e)
                raise

        # ================= Listener =================
        try:
            listener = QueueListener(
                log_queue,
                *handlers,
                respect_handler_level=True
            )
            listener.start()
            print("🚀 [LOGGER] QueueListener démarré")
        except Exception as e:
            print("❌ [LOGGER] Erreur QueueListener:", e)
            raise

        DevLogger._logger = logger
        DevLogger._listener = listener
        DevLogger._queue = log_queue

        print("🎉 [LOGGER] Logger prêt à l'utilisation")
        print("✅ Async Logger initialisé avec succès")

    # =========================
    # Méthodes de log
    # =========================

    @staticmethod
    def debug(msg: str):
        if DevLogger._logger:
            print(f"🐞 [DEBUG] {msg}")
            DevLogger._logger.debug(msg)
        else:
            print("⚠️ [DEBUG] Logger non initialisé")

    @staticmethod
    def info(msg: str):
        if DevLogger._logger:
            print(f"ℹ️ [INFO] {msg}")
            DevLogger._logger.info(msg)

    @staticmethod
    def warning(msg: str):
        if DevLogger._logger:
            print(f"⚠️ [WARNING] {msg}")
            DevLogger._logger.warning(msg)

    @staticmethod
    def error(msg: str):
        if DevLogger._logger:
            print(f"❌ [ERROR] {msg}")
            DevLogger._logger.error(msg)

    @staticmethod
    def critical(msg: str):
        if DevLogger._logger:
            print(f"🔥 [CRITICAL] {msg}")
            DevLogger._logger.critical(msg)

    @staticmethod
    def exception(msg: str):
        if DevLogger._logger:
            print(f"💥 [EXCEPTION] {msg}")
            DevLogger._logger.exception(msg)

    # =========================
    # Mesure de temps
    # =========================

    @staticmethod
    def log_time(msg: str, start_time: float):
        elapsed = time.time() - start_time
        print(f"⏱️ [TIMER] {msg} → {elapsed:.3f}s")
        print(f"{msg} | Temps écoulé : {elapsed:.3f}s")
        return elapsed

    # =========================
    # Arrêt propre
    # =========================

    @staticmethod
    def shutdown():
        print("🛑 [LOGGER] Arrêt du logger...")
        if DevLogger._listener:
            DevLogger._listener.stop()
            DevLogger._listener = None
            DevLogger._logger = None
            DevLogger._queue = None
            print("✅ [LOGGER] Logger arrêté proprement")


DevLogger = DevLogger()
