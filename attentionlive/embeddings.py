import hashlib
import random


def word_seed(word, salt):
    """Derive a deterministic integer seed from a word, independent of the
    process's hash randomization (plain hash() is salted per-process)."""
    digest = hashlib.sha256(f"{salt}:{word.lower()}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def embed(word, dim, salt="attentionlive-embed"):
    """Return a deterministic pseudo-random embedding vector for a word."""
    rng = random.Random(word_seed(word, salt))
    return [rng.gauss(0.0, 1.0) for _ in range(dim)]
