import re

_WORD_RE = re.compile(r"[A-Za-z0-9']+|[.,!?;:]")


def tokenize(text):
    """Split a sentence into words and punctuation marks, in order."""
    return _WORD_RE.findall(text)
