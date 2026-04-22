"""Thread-safe JS dispatcher — queue events from worker threads, drain on a single thread."""
import json
import queue
import threading


class JsDispatcher:
    def __init__(self):
        self.q = queue.Queue()
        self.window = None
        self.stop_event = threading.Event()
        self.thread = None

    def attach(self, window):
        self.window = window
        self.thread = threading.Thread(target=self._drain, daemon=True)
        self.thread.start()

    def _drain(self):
        while not self.stop_event.is_set():
            try:
                script = self.q.get(timeout=0.5)
            except queue.Empty:
                continue
            if script is None:
                return
            if self.window is None:
                continue
            try:
                self.window.evaluate_js(script)
            except Exception:
                pass

    def emit(self, fn_name, payload):
        if self.window is None:
            return
        try:
            encoded = json.dumps(payload, default=str)
        except (TypeError, ValueError):
            encoded = json.dumps({"error": "unserializable payload"})
        script = f"window.__onEvent && window.__onEvent({json.dumps(fn_name)}, {encoded});"
        self.q.put(script)

    def stop(self):
        self.stop_event.set()
        self.q.put(None)


_dispatcher = JsDispatcher()


def get_dispatcher():
    return _dispatcher
