from collections import deque


class SharedRuntimeState:
    """Mutable collections shared by the application runtime."""

    def __init__(self):
        self.firefox_sessions = {}
        self.logs = deque()
        self.process_pids = []
        self.notification_badges = {}
        self.active_emails = set()
        self.logs_running = True
        self.remaining_emails = 0
        self.selected_browser = None


runtime_state = SharedRuntimeState()
