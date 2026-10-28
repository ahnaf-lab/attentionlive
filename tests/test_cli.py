import contextlib
import io
import os
import tempfile
import unittest

from attentionlive.cli import main


def _run_cli(argv):
    """Run the CLI with argv, returning (exit_code, stdout)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = main(argv)
    return code, out.getvalue()


class RunSubcommandTests(unittest.TestCase):
    def test_run_with_explicit_text_prints_its_tokens(self):
        code, out = _run_cli(["run", "cat", "sees", "dog"])
        self.assertEqual(code, 0)
        self.assertIn("'cat'", out)
        self.assertIn("'sees'", out)
        self.assertIn("'dog'", out)

    def test_run_without_text_falls_back_to_default_sentence(self):
        code, out = _run_cli(["run"])
        self.assertEqual(code, 0)
        self.assertIn("'cat'", out)

    def test_run_output_is_deterministic(self):
        _, first = _run_cli(["run", "a", "fixed", "sentence"])
        _, second = _run_cli(["run", "a", "fixed", "sentence"])
        self.assertEqual(first, second)


class SvgSubcommandTests(unittest.TestCase):
    def test_svg_writes_well_formed_svg_markup_to_stdout(self):
        code, out = _run_cli(["svg", "cat sees dog"])
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("<svg"))
        self.assertIn("</svg>", out)

    def test_svg_respects_size_flags(self):
        code, out = _run_cli(["svg", "cat sees dog", "--width", "100", "--height", "50"])
        self.assertEqual(code, 0)
        self.assertIn('width="100"', out)
        self.assertIn('height="50"', out)


class ParserTests(unittest.TestCase):
    def test_unknown_subcommand_is_rejected(self):
        with self.assertRaises(SystemExit):
            _run_cli(["not-a-real-command"])

    def test_no_subcommand_is_rejected(self):
        with self.assertRaises(SystemExit):
            _run_cli([])


class WatchSubcommandTests(unittest.TestCase):
    def test_watch_prints_its_addresses_before_serving(self):
        fd, path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        with open(path, "w") as f:
            f.write("hello")
        self.addCleanup(os.unlink, path)

        import threading

        original_serve_target = "attentionlive.cli.serve"
        import attentionlive.cli as cli_module

        stop_immediately = threading.Event()
        stop_immediately.set()

        real_serve = cli_module.serve

        def fake_serve(path, host, port, poll_interval):
            return real_serve(path, host=host, port=port,
                               poll_interval=poll_interval, stop_event=stop_immediately)

        cli_module.serve = fake_serve
        try:
            code, out = _run_cli(["watch", path, "--port", "0"])
        finally:
            cli_module.serve = real_serve

        self.assertEqual(code, 0)
        self.assertIn(f"watching {path!r}", out)
        self.assertIn("/events", out)


if __name__ == "__main__":
    unittest.main()
