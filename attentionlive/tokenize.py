import re

# A "word" is a run of letters/digits (unicode-aware, so accented and
# non-Latin scripts count), optionally linked by a single apostrophe or
# hyphen to another such run ("don't", "well-known", "café"). Anything else
# that isn't whitespace falls through to the second branch as its own
# single-character token, so no character from arbitrary input is dropped.
_WORD_RE = re.compile(r"[^\W_]+(?:['’-][^\W_]+)*|[^\s\w]")


def tokenize(text):
    """Split text into words and individual punctuation/symbol marks, in order."""
    return _WORD_RE.findall(text)
