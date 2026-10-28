"""Watch a scratch file and serve recomputed attention weights over SSE."""

import argparse
import hashlib
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from queue import Queue

from .attention import run_attention

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
DEFAULT_POLL_INTERVAL = 0.3


def _file_fingerprint(path):
    """Return (content_hash, text) for path, or None if it can't be read."""
    try:
        with open(path, "rb") as f:
            data = f.read()
    except (FileNotFoundError, IsADirectoryError, PermissionError):
        return None
    return hashlib.sha256(data).hexdigest(), data.decode("utf-8", errors="replace")


def build_payload(text):
    """Recompute attention over text and return a JSON-serializable payload."""
    result = run_attention(text)
    return {
        "text": text,
        "tokens": result["tokens"],
        "weights": result["weights"],
    }


class ScratchWatcher:
    """Polls a scratch file for content changes.

    Uses a content hash rather than mtime, since two quick consecutive
    saves can land within the filesystem's mtime resolution window and
    would otherwise look like a single save.
    """

    def __init__(self, path, poll_interval=DEFAULT_POLL_INTERVAL):
        self.path = path
        self.poll_interval = poll_interval
        self._last_hash = None

    def poll_once(self):
        """Check the file once. Return new text if its content changed
        since the last call (including the very first call), else None."""
        fingerprint = _file_fingerprint(self.path)
        if fingerprint is None:
            return None
        content_hash, text = fingerprint
        if content_hash == self._last_hash:
            return None
        self._last_hash = content_hash
        return text

    def run(self, on_change, stop_event):
        """Poll until stop_event is set, calling on_change(text) per change."""
        while not stop_event.is_set():
            text = self.poll_once()
            if text is not None:
                on_change(text)
            stop_event.wait(self.poll_interval)


class SSEBroadcaster:
    """Fans a stream of JSON-encoded payloads out to subscribed queues."""

    def __init__(self):
        self._subscribers = []
        self._lock = threading.Lock()

    def subscribe(self):
        q = Queue()
        with self._lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q):
        with self._lock:
            if q in self._subscribers:
                self._subscribers.remove(q)

    def broadcast(self, payload):
        data = json.dumps(payload)
        with self._lock:
            subscribers = list(self._subscribers)
        for q in subscribers:
            q.put(data)


def make_handler(broadcaster):
    """Build a request handler bound to broadcaster, serving /events as SSE."""

    class SSEHandler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            pass

        def do_GET(self):
            if self.path != "/events":
                self.send_response(404)
                self.end_headers()
                return

            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            q = broadcaster.subscribe()
            try:
                while True:
                    data = q.get()
                    self.wfile.write(f"data: {data}\n\n".encode("utf-8"))
                    self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                broadcaster.unsubscribe(q)

    return SSEHandler


def serve(path, host=DEFAULT_HOST, port=DEFAULT_PORT,
          poll_interval=DEFAULT_POLL_INTERVAL, stop_event=None):
    """Watch path and serve an SSE stream of attention payloads until stopped.

    Binds to host/port (127.0.0.1 by default, so the stream is reachable
    only from this machine) and blocks until stop_event is set.
    """
    stop_event = stop_event or threading.Event()
    broadcaster = SSEBroadcaster()
    watcher = ScratchWatcher(path, poll_interval=poll_interval)

    httpd = ThreadingHTTPServer((host, port), make_handler(broadcaster))
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()

    def on_change(text):
        broadcaster.broadcast(build_payload(text))

    try:
        watcher.run(on_change, stop_event)
    finally:
        httpd.shutdown()
        httpd.server_close()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(
        prog="python3 -m attentionlive.watch",
        description=(
            "Watch a scratch text file and stream recomputed attention "
            "weights as JSON over local SSE on every save."
        ),
    )
    parser.add_argument("path", help="path to the scratch text file to watch")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL,
        dest="poll_interval",
    )
    args = parser.parse_args(argv)

    print(f"watching {args.path!r}")
    print(f"SSE stream: http://{args.host}:{args.port}/events")
    try:
        serve(args.path, host=args.host, port=args.port,
              poll_interval=args.poll_interval)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
