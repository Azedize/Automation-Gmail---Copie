from queue import Queue

from watchdog.events import FileSystemEventHandler


class DownloadFileEventHandler(FileSystemEventHandler):
    def __init__(self, file_queue: Queue):
        super().__init__()
        self.file_queue = file_queue

    def on_created(self, event):
        if not event.is_directory:
            self.file_queue.put(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            self.file_queue.put(event.dest_path)
