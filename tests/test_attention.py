import unittest

from attentionlive.attention import AttentionHead, run_attention
from attentionlive.embeddings import embed


class AttentionDeterminismTests(unittest.TestCase):
    def test_same_text_gives_identical_weights_across_runs(self):
        a = run_attention("the cat sat on the mat")
        b = run_attention("the cat sat on the mat")
        self.assertEqual(a["weights"], b["weights"])

    def test_same_word_has_same_embedding_in_different_sentences(self):
        first = embed("cat", dim=16)
        second = embed("cat", dim=16)
        self.assertEqual(first, second)

    def test_different_words_get_different_embeddings(self):
        self.assertNotEqual(embed("cat", dim=16), embed("dog", dim=16))


class AttentionShapeTests(unittest.TestCase):
    def setUp(self):
        self.result = run_attention("red dogs run fast")

    def test_weights_matrix_is_n_by_n(self):
        n = len(self.result["tokens"])
        weights = self.result["weights"]
        self.assertEqual(len(weights), n)
        for row in weights:
            self.assertEqual(len(row), n)

    def test_attention_rows_sum_to_one(self):
        for row in self.result["weights"]:
            self.assertAlmostEqual(sum(row), 1.0, places=9)

    def test_attention_weights_are_non_negative(self):
        for row in self.result["weights"]:
            for w in row:
                self.assertGreaterEqual(w, 0.0)

    def test_output_matrix_has_one_vector_per_token(self):
        n = len(self.result["tokens"])
        self.assertEqual(len(self.result["output"]), n)
        for vec in self.result["output"]:
            self.assertEqual(len(vec), 16)

    def test_empty_text_produces_empty_result(self):
        result = run_attention("")
        self.assertEqual(result["tokens"], [])
        self.assertEqual(result["weights"], [])
        self.assertEqual(result["output"], [])


class AttentionHeadSeedTests(unittest.TestCase):
    def test_different_seeds_give_different_projection_matrices(self):
        head_a = AttentionHead(seed=1)
        head_b = AttentionHead(seed=2)
        self.assertNotEqual(head_a.w_query, head_b.w_query)

    def test_same_seed_gives_same_projection_matrices(self):
        head_a = AttentionHead(seed=42)
        head_b = AttentionHead(seed=42)
        self.assertEqual(head_a.w_query, head_b.w_query)
        self.assertEqual(head_a.w_key, head_b.w_key)
        self.assertEqual(head_a.w_value, head_b.w_value)

    def test_reordering_tokens_changes_attention_pattern(self):
        head = AttentionHead(seed=7)
        forward = head.forward(["cat", "chases", "mouse"])
        backward = head.forward(["mouse", "chases", "cat"])
        self.assertNotEqual(forward["weights"], backward["weights"])


if __name__ == "__main__":
    unittest.main()
