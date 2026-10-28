"""Render a fixed sentence's attention weights as a static, standalone SVG.

Unlike the live page (page.py), which pushes JSON over SSE and animates in
the browser, this module computes plain SVG markup entirely in Python: the
same tokens and weights always produce byte-for-byte the same markup, which
is what makes it possible to pin exact output in golden tests.
"""

import argparse
import sys

from .attention import DEFAULT_DIM, DEFAULT_PROJECTION_SEED, run_attention

DEFAULT_WIDTH = 720
DEFAULT_HEIGHT = 360
DEFAULT_MARGIN = 72


def _token_positions(n, width, height, margin):
    if n <= 1:
        return [(width / 2.0, height / 2.0) for _ in range(n)]
    usable = width - 2 * margin
    return [
        (margin + usable * i / (n - 1), height / 2.0)
        for i in range(n)
    ]


def _pair_weights(weights):
    """Average weight for each unordered token pair i<j, and its max."""
    n = len(weights)
    pairs = []
    max_weight = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            w = (weights[i][j] + weights[j][i]) / 2.0
            pairs.append((i, j, w))
            if w > max_weight:
                max_weight = w
    return pairs, max_weight


def _escape(text):
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_svg(tokens, weights, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
               margin=DEFAULT_MARGIN):
    """Render tokens and their attention weight matrix as a static SVG string.

    Output is a pure function of (tokens, weights, width, height, margin):
    no timestamps, randomness, or dict/set iteration order is involved, so
    the same inputs always produce the same markup exactly.
    """
    n = len(tokens)
    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#0b0d12"/>',
    ]

    if n == 0:
        lines.append("</svg>")
        return "\n".join(lines) + "\n"

    positions = _token_positions(n, width, height, margin)
    pairs, max_weight = _pair_weights(weights)
    max_weight = max_weight or 0.0001

    lines.append('<g stroke="#6ad7ff">')
    for i, j, w in pairs:
        x1, y1 = positions[i]
        x2, y2 = positions[j]
        rel = w / max_weight
        opacity = 0.05 + 0.9 * rel
        stroke_width = 0.5 + 4.5 * rel
        lines.append(
            f'<line x1="{x1:.2f}" y1="{y1:.2f}" x2="{x2:.2f}" y2="{y2:.2f}" '
            f'stroke-opacity="{opacity:.3f}" stroke-width="{stroke_width:.2f}"/>'
        )
    lines.append("</g>")

    lines.append('<g fill="#e7e9ee" font-family="sans-serif" font-size="20" '
                  'text-anchor="middle">')
    for token, (x, y) in zip(tokens, positions):
        lines.append(
            f'<text x="{x:.2f}" y="{y:.2f}" dominant-baseline="middle">'
            f'{_escape(token)}</text>'
        )
    lines.append("</g>")

    lines.append("</svg>")
    return "\n".join(lines) + "\n"


def render_svg_for_text(text, dim=DEFAULT_DIM, seed=DEFAULT_PROJECTION_SEED,
                         width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT,
                         margin=DEFAULT_MARGIN):
    """Tokenize text, run attention over it, and render the result as SVG."""
    result = run_attention(text, dim=dim, seed=seed)
    return render_svg(result["tokens"], result["weights"],
                       width=width, height=height, margin=margin)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(
        prog="python3 -m attentionlive.svg",
        description="Render a sentence's attention weights as a static SVG.",
    )
    parser.add_argument("text", help="sentence to render")
    parser.add_argument("--width", type=int, default=DEFAULT_WIDTH)
    parser.add_argument("--height", type=int, default=DEFAULT_HEIGHT)
    parser.add_argument("--margin", type=int, default=DEFAULT_MARGIN)
    args = parser.parse_args(argv)

    sys.stdout.write(
        render_svg_for_text(args.text, width=args.width, height=args.height,
                             margin=args.margin)
    )


if __name__ == "__main__":
    main()
