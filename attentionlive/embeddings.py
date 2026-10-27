import hashlib
import random


def word_seed(word, salt):
    """Derive a deterministic integer seed from a word, independent of the
    process's hash randomization (plain hash() is salted per-process)."""
    digest = hashlib.sha256(f"{salt}:{word.lower()}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def embed(word, dim, salt="attentionlive-embed"):
    """Return a deterministic pseudo-random embedding vector for a word.

    Works for any string, not just dictionary words: punctuation tokens,
    numbers, and unicode text all hash to a stable vector the same way.
    """
    rng = random.Random(word_seed(word, salt))
    return [rng.gauss(0.0, 1.0) for _ in range(dim)]


class EmbeddingTable:
    """A memoized seeded embedding lookup for a fixed dimension and salt.

    Repeated tokens (common in short scratch-file sentences, e.g. "the")
    are hashed and sampled only once per table instance.
    """

    def __init__(self, dim, salt="attentionlive-embed"):
        self.dim = dim
        self.salt = salt
        self._cache = {}

    def lookup(self, word):
        """Return the embedding for word, computing and caching it on first use."""
        key = word.lower()
        vector = self._cache.get(key)
        if vector is None:
            vector = embed(word, self.dim, self.salt)
            self._cache[key] = vector
        return vector

    def lookup_many(self, words):
        """Return the list of embeddings for words, in order."""
        return [self.lookup(word) for word in words]
