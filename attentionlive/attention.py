import math
import random

from .embeddings import EmbeddingTable
from .tokenize import tokenize

DEFAULT_DIM = 16
DEFAULT_PROJECTION_SEED = 1337


def _random_matrix(rows, cols, seed):
    rng = random.Random(seed)
    scale = 1.0 / math.sqrt(cols)
    return [[rng.gauss(0.0, scale) for _ in range(cols)] for _ in range(rows)]


def _matmul(a, b):
    """Multiply matrix a (n x k) by matrix b (k x m) -> n x m."""
    n, k = len(a), len(a[0])
    k2, m = len(b), len(b[0])
    assert k == k2, "inner dimensions must match"
    out = [[0.0] * m for _ in range(n)]
    for i in range(n):
        row = a[i]
        for p in range(k):
            v = row[p]
            if v == 0.0:
                continue
            brow = b[p]
            orow = out[i]
            for j in range(m):
                orow[j] += v * brow[j]
    return out


def _transpose(a):
    return [list(col) for col in zip(*a)]


def _softmax_rows(matrix):
    out = []
    for row in matrix:
        m = max(row)
        exps = [math.exp(x - m) for x in row]
        total = sum(exps)
        out.append([x / total for x in exps])
    return out


class AttentionHead:
    """A single, untrained, seeded-deterministic self-attention head.

    Projection matrices are fixed by a seed, so the same text always
    produces the same attention weights and output.
    """

    def __init__(self, dim=DEFAULT_DIM, d_k=None, seed=DEFAULT_PROJECTION_SEED):
        self.dim = dim
        self.d_k = d_k or dim
        self.seed = seed
        self.w_query = _random_matrix(dim, self.d_k, seed)
        self.w_key = _random_matrix(dim, self.d_k, seed + 1)
        self.w_value = _random_matrix(dim, self.d_k, seed + 2)
        self.embedding_table = EmbeddingTable(dim)

    def embed_tokens(self, tokens):
        return self.embedding_table.lookup_many(tokens)

    def forward(self, tokens):
        if not tokens:
            return {"tokens": [], "weights": [], "output": []}

        x = self.embed_tokens(tokens)
        q = _matmul(x, self.w_query)
        k = _matmul(x, self.w_key)
        v = _matmul(x, self.w_value)

        scores = _matmul(q, _transpose(k))
        scale = math.sqrt(self.d_k)
        scaled = [[s / scale for s in row] for row in scores]
        weights = _softmax_rows(scaled)
        output = _matmul(weights, v)

        return {"tokens": tokens, "weights": weights, "output": output}


def run_attention(text, dim=DEFAULT_DIM, seed=DEFAULT_PROJECTION_SEED):
    """Tokenize text and run a single attention head over it."""
    tokens = tokenize(text)
    head = AttentionHead(dim=dim, seed=seed)
    return head.forward(tokens)
