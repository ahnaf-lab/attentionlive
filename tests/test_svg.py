import unittest

from attentionlive.attention import run_attention
from attentionlive.svg import render_svg, render_svg_for_text

GOLDEN_TEXT = "cat sees dog"

GOLDEN_TOKENS = ["cat", "sees", "dog"]

GOLDEN_WEIGHTS = [
    [0.08747490668046433, 0.22952636572402463, 0.6829987275955111],
    [0.04775453451797325, 0.13203191203238063, 0.8202135534496462],
    [0.10314335487093809, 0.839251967588676, 0.05760467754038598],
]

GOLDEN_SVG = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="360" '
    'viewBox="0 0 720 360">\n'
    '<rect width="100%" height="100%" fill="#0b0d12"/>\n'
    '<g stroke="#6ad7ff">\n'
    '<line x1="72.00" y1="180.00" x2="360.00" y2="180.00" '
    'stroke-opacity="0.200" stroke-width="1.25"/>\n'
    '<line x1="72.00" y1="180.00" x2="648.00" y2="180.00" '
    'stroke-opacity="0.476" stroke-width="2.63"/>\n'
    '<line x1="360.00" y1="180.00" x2="648.00" y2="180.00" '
    'stroke-opacity="0.950" stroke-width="5.00"/>\n'
    '</g>\n'
    '<g fill="#e7e9ee" font-family="sans-serif" font-size="20" '
    'text-anchor="middle">\n'
    '<text x="72.00" y="180.00" dominant-baseline="middle">cat</text>\n'
    '<text x="360.00" y="180.00" dominant-baseline="middle">sees</text>\n'
    '<text x="648.00" y="180.00" dominant-baseline="middle">dog</text>\n'
    '</g>\n'
    '</svg>\n'
)

GOLDEN_SVG_SINGLE_TOKEN = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="360" '
    'viewBox="0 0 720 360">\n'
    '<rect width="100%" height="100%" fill="#0b0d12"/>\n'
    '<g stroke="#6ad7ff">\n'
    '</g>\n'
    '<g fill="#e7e9ee" font-family="sans-serif" font-size="20" '
    'text-anchor="middle">\n'
    '<text x="360.00" y="180.00" dominant-baseline="middle">hi</text>\n'
    '</g>\n'
    '</svg>\n'
)

GOLDEN_SVG_EMPTY = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="720" height="360" '
    'viewBox="0 0 720 360">\n'
    '<rect width="100%" height="100%" fill="#0b0d12"/>\n'
    '</svg>\n'
)


class GoldenAttentionMatrixTests(unittest.TestCase):
    """A fixed sentence must always produce exactly the same tokens and
    attention matrix: these were captured once from a known-good run and
    are asserted verbatim, so any change to the core silently shifting the
    numbers gets caught."""

    def test_fixed_sentence_gives_exact_tokens(self):
        result = run_attention(GOLDEN_TEXT)
        self.assertEqual(result["tokens"], GOLDEN_TOKENS)

    def test_fixed_sentence_gives_exact_attention_matrix(self):
        result = run_attention(GOLDEN_TEXT)
        self.assertEqual(result["weights"], GOLDEN_WEIGHTS)


class GoldenSvgOutputTests(unittest.TestCase):
    """The same fixed sentence must render to exactly the same SVG markup,
    byte for byte."""

    def test_fixed_sentence_gives_exact_svg(self):
        self.assertEqual(render_svg_for_text(GOLDEN_TEXT), GOLDEN_SVG)

    def test_rendering_the_golden_matrix_directly_matches_too(self):
        self.assertEqual(
            render_svg(GOLDEN_TOKENS, GOLDEN_WEIGHTS), GOLDEN_SVG
        )

    def test_single_token_gives_exact_svg(self):
        self.assertEqual(render_svg_for_text("hi"), GOLDEN_SVG_SINGLE_TOKEN)

    def test_empty_text_gives_exact_svg(self):
        self.assertEqual(render_svg_for_text(""), GOLDEN_SVG_EMPTY)


class SvgStructureTests(unittest.TestCase):
    def test_svg_escapes_markup_characters_in_tokens(self):
        out = render_svg(["<", "&"], [[0.5, 0.5], [0.5, 0.5]])
        self.assertIn(">&lt;<", out)
        self.assertIn(">&amp;<", out)
        self.assertNotIn("<<", out)

    def test_rendering_is_deterministic_across_calls(self):
        first = render_svg_for_text(GOLDEN_TEXT)
        second = render_svg_for_text(GOLDEN_TEXT)
        self.assertEqual(first, second)

    def test_different_text_renders_different_svg(self):
        self.assertNotEqual(
            render_svg_for_text(GOLDEN_TEXT),
            render_svg_for_text("a totally different sentence"),
        )


if __name__ == "__main__":
    unittest.main()
