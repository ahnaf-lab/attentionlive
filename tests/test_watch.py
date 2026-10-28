import json
import os
import socket
import tempfile
import threading
import time
import unittest

from attentionlive.attention import run_attention
from attentionlive.watch import (
    ScratchWatcher,
    SSEBroadcaster,
    build_payload,
    serve,
)


def _atomic_write(path, text):
    """Write text to path via a temp file + rename, so a concurrent reader
    never observes a transiently truncated or partially-written file."""
    directory = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(dir=directory)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.replace(tmp_path, path)
    except Exception:
        os.unlink(tmp_path)
        raise


class ScratchWatcherTests(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        with open(self.path, "w") as f:
            f.write("the cat sat")
        self.addCleanup(os.unlink, self.path)

    def test_first_poll_reports_existing_content(self):
        watcher = ScratchWatcher(self.path)
        self.assertEqual(watcher.poll_once(), "the cat sat")

    def test_unchanged_content_polls_as_no_change(self):
        watcher = ScratchWatcher(self.path)
        watcher.poll_once()
        self.assertIsNone(watcher.poll_once())

    def test_changed_content_is_reported_once(self):
        watcher = ScratchWatcher(self.path)
        watcher.poll_once()
        with open(self.path, "w") as f:
            f.write("the dog ran")
        self.assertEqual(watcher.poll_once(), "the dog ran")
        self.assertIsNone(watcher.poll_once())

    def test_missing_file_polls_as_no_change(self):
        watcher = ScratchWatcher(os.path.join(tempfile.gettempdir(), "does-not-exist.txt"))
        self.assertIsNone(watcher.poll_once())


class SSEBroadcasterTests(unittest.TestCase):
    def test_subscriber_receives_broadcast_payload(self):
        broadcaster = SSEBroadcaster()
        q = broadcaster.subscribe()
        broadcaster.broadcast({"tokens": ["a", "b"]})
        self.assertEqual(json.loads(q.get(timeout=1)), {"tokens": ["a", "b"]})

    def test_all_subscribers_receive_the_same_broadcast(self):
        broadcaster = SSEBroadcaster()
        q1 = broadcaster.subscribe()
        q2 = broadcaster.subscribe()
        broadcaster.broadcast({"text": "hi"})
        self.assertEqual(json.loads(q1.get(timeout=1)), {"text": "hi"})
        self.assertEqual(json.loads(q2.get(timeout=1)), {"text": "hi"})

    def test_unsubscribed_queue_gets_no_further_broadcasts(self):
        broadcaster = SSEBroadcaster()
        q = broadcaster.subscribe()
        broadcaster.unsubscribe(q)
        broadcaster.broadcast({"text": "ignored"})
        self.assertTrue(q.empty())


class BuildPayloadTests(unittest.TestCase):
    def test_payload_matches_attention_core_output(self):
        payload = build_payload("red dogs run")
        expected = run_attention("red dogs run")
        self.assertEqual(payload["text"], "red dogs run")
        self.assertEqual(payload["tokens"], expected["tokens"])
        self.assertEqual(payload["weights"], expected["weights"])

    def test_payload_is_json_serializable(self):
        payload = build_payload("hello, world!")
        encoded = json.dumps(payload)
        self.assertEqual(json.loads(encoded)["tokens"], payload["tokens"])


class SSEDaemonIntegrationTests(unittest.TestCase):
    def test_file_save_is_broadcast_to_sse_client_as_json(self):
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        _atomic_write(path, "cat sees dog")

        with socket.socket() as probe:
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]

        stop_event = threading.Event()
        thread = threading.Thread(
            target=serve,
            kwargs=dict(
                path=path,
                host="127.0.0.1",
                port=port,
                poll_interval=0.05,
                stop_event=stop_event,
            ),
            daemon=True,
        )
        thread.start()

        sock = None
        try:
            sock = self._connect_with_retry("127.0.0.1", port)
            sock.sendall(b"GET /events HTTP/1.1\r\nHost: localhost\r\n\r\n")

            buf = b""
            header_blob, buf = self._recv_until(sock, b"\r\n\r\n", buf)
            self.assertIn(b"200", header_blob.splitlines()[0])

            # The watcher's very first poll (racing against our subscribe
            # above) may or may not reach us; only the change made below,
            # after the connection is confirmed open, is relied on.
            _atomic_write(path, "dog sees cat")

            event, buf = self._recv_until(sock, b"\n\n", buf)
            line = event.decode("utf-8").strip()
            self.assertTrue(line.startswith("data: "))
            payload = json.loads(line[len("data: "):])
            self.assertEqual(payload["text"], "dog sees cat")
            self.assertEqual(payload["tokens"], ["dog", "sees", "cat"])
        finally:
            if sock is not None:
                sock.close()
            stop_event.set()
            thread.join(timeout=5)
            os.unlink(path)

    def _connect_with_retry(self, host, port, timeout=5):
        deadline = time.time() + timeout
        last_error = None
        while time.time() < deadline:
            try:
                sock = socket.create_connection((host, port), timeout=1)
                sock.settimeout(5)
                return sock
            except OSError as exc:
                last_error = exc
                time.sleep(0.05)
        raise last_error

    def _recv_until(self, sock, marker, buf):
        while marker not in buf:
            chunk = sock.recv(4096)
            if not chunk:
                raise ConnectionError("connection closed before marker found")
            buf += chunk
        idx = buf.index(marker) + len(marker)
        return buf[:idx], buf[idx:]


if __name__ == "__main__":
    unittest.main()
