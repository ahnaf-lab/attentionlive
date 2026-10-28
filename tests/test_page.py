import http.client
import os
import socket
import tempfile
import threading
import time
import unittest

from attentionlive.page import PAGE_HTML, PAGE_HTML_BYTES
from attentionlive.watch import serve


class PageContentTests(unittest.TestCase):
    def test_page_sets_up_an_svg_stage(self):
        self.assertIn('<svg id="stage"', PAGE_HTML)

    def test_page_subscribes_to_the_events_stream(self):
        self.assertIn('new EventSource("/events")', PAGE_HTML)

    def test_page_bytes_are_the_utf8_encoding_of_the_html(self):
        self.assertEqual(PAGE_HTML_BYTES, PAGE_HTML.encode("utf-8"))

    def test_page_draws_edges_scaled_by_attention_weight(self):
        self.assertIn("stroke-opacity", PAGE_HTML)
        self.assertIn("stroke-width", PAGE_HTML)


class PageServingIntegrationTests(unittest.TestCase):
    def test_root_path_serves_the_html_page(self):
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        with open(path, "w") as f:
            f.write("cat sees dog")

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

        conn = None
        try:
            conn = self._connect_with_retry("127.0.0.1", port)
            conn.request("GET", "/")
            response = conn.getresponse()
            body = response.read()

            self.assertEqual(response.status, 200)
            self.assertIn("text/html", response.getheader("Content-Type"))
            self.assertEqual(body, PAGE_HTML_BYTES)
        finally:
            if conn is not None:
                conn.close()
            stop_event.set()
            thread.join(timeout=5)
            os.unlink(path)

    def _connect_with_retry(self, host, port, timeout=5):
        deadline = time.time() + timeout
        last_error = None
        while time.time() < deadline:
            conn = http.client.HTTPConnection(host, port, timeout=1)
            try:
                conn.connect()
                return conn
            except OSError as exc:
                conn.close()
                last_error = exc
                time.sleep(0.05)
        raise last_error


if __name__ == "__main__":
    unittest.main()
