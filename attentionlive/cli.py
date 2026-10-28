"""Single command-line entry point for attentionlive.

Dispatches to the three ways of using the tool: printing a sentence's
attention weights once (`run`), watching a scratch file and serving them
live over SSE (`watch`), and rendering a one-off static SVG (`svg`). This
is what the installed `attentionlive` script resolves to, so a user never
has to know the package's internal module layout.
"""

import argparse
import sys

from .attention import run_attention
from .svg import DEFAULT_HEIGHT, DEFAULT_MARGIN, DEFAULT_WIDTH, render_svg_for_text
from .watch import DEFAULT_HOST, DEFAULT_POLL_INTERVAL, DEFAULT_PORT, serve

DEFAULT_TEXT = "the cat sat on the mat"


def _run(args):
    text = " ".join(args.text) if args.text else DEFAULT_TEXT
    result = run_attention(text)
    tokens = result["tokens"]
    print("tokens:", tokens)
    for i, row in enumerate(result["weights"]):
        formatted = ", ".join(f"{w:.3f}" for w in row)
        print(f"{tokens[i]!r:>12}: [{formatted}]")
    return 0


def _watch(args):
    print(f"watching {args.path!r}")
    print(f"live page: http://{args.host}:{args.port}/")
    print(f"SSE stream: http://{args.host}:{args.port}/events")
    try:
        serve(args.path, host=args.host, port=args.port,
              poll_interval=args.poll_interval)
    except KeyboardInterrupt:
        pass
    return 0


def _svg(args):
    sys.stdout.write(
        render_svg_for_text(args.text, width=args.width, height=args.height,
                             margin=args.margin)
    )
    return 0


def _build_parser():
    parser = argparse.ArgumentParser(
        prog="attentionlive",
        description=(
            "Poke at a hand-rolled, untrained, seeded-deterministic "
            "self-attention head with your own sentences."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run", help="print the attention weight matrix for a sentence")
    run_parser.add_argument(
        "text", nargs="*",
        help=f"sentence to run attention over (default: {DEFAULT_TEXT!r})")
    run_parser.set_defaults(handler=_run)

    watch_parser = subparsers.add_parser(
        "watch",
        help="watch a scratch file and stream live attention weights over SSE")
    watch_parser.add_argument("path", help="path to the scratch text file to watch")
    watch_parser.add_argument("--host", default=DEFAULT_HOST)
    watch_parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    watch_parser.add_argument(
        "--poll-interval", type=float, default=DEFAULT_POLL_INTERVAL,
        dest="poll_interval")
    watch_parser.set_defaults(handler=_watch)

    svg_parser = subparsers.add_parser(
        "svg", help="render a sentence's attention weights as a static SVG")
    svg_parser.add_argument("text", help="sentence to render")
    svg_parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    svg_parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    svg_parser.add_argument("--margin", type=int, default=DEFAULT_MARGIN)
    svg_parser.set_defaults(handler=_svg)

    return parser


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = _build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
