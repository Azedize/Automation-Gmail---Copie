import time

from PyQt6.QtCore import QThread, pyqtSignal


class ApplicationLogDisplayThread(QThread):
    log_signal = pyqtSignal(str)

    def __init__(self, logs, is_running, parent=None):
        super().__init__(parent)
        self.LOGS = logs
        self.is_running = is_running
        self.stop_flag = False

    def run(self):
        while self.is_running() and not self.stop_flag:
            if self.LOGS:
                self.log_signal.emit(self.LOGS.popleft())
            else:
                time.sleep(1)

    def stopThread(self):
        self.stop_flag = True
        self.wait()
