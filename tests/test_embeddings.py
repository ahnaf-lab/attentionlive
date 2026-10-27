import unittest

from attentionlive.embeddings import EmbeddingTable, embed, word_seed


class EmbedFunctionTests(unittest.TestCase):
    def test_vector_has_requested_dimension(self):
        self.assertEqual(len(embed("hello", dim=8)), 8)

    def test_same_word_and_dim_is_deterministic(self):
        self.assertEqual(embed("hello", dim=12), embed("hello", dim=12))

    def test_case_insensitive(self):
        self.assertEqual(embed("Hello", dim=8), embed("hello", dim=8))

    def test_different_words_differ(self):
        self.assertNotEqual(embed("hello", dim=8), embed("goodbye", dim=8))

    def test_different_salts_give_different_embeddings(self):
        a = embed("hello", dim=8, salt="salt-a")
        b = embed("hello", dim=8, salt="salt-b")
        self.assertNotEqual(a, b)

    def test_handles_punctuation_and_digits(self):
        self.assertEqual(len(embed(",", dim=8)), 8)
        self.assertEqual(len(embed("42", dim=8)), 8)

    def test_handles_unicode_input(self):
        vector = embed("café", dim=8)
        self.assertEqual(len(vector), 8)
        self.assertEqual(vector, embed("café", dim=8))

    def test_handles_empty_string(self):
        self.assertEqual(len(embed("", dim=8)), 8)


class WordSeedTests(unittest.TestCase):
    def test_seed_is_deterministic(self):
        self.assertEqual(word_seed("cat", "s"), word_seed("cat", "s"))

    def test_seed_is_case_insensitive(self):
        self.assertEqual(word_seed("Cat", "s"), word_seed("cat", "s"))

    def test_seed_differs_by_word(self):
        self.assertNotEqual(word_seed("cat", "s"), word_seed("dog", "s"))


class EmbeddingTableTests(unittest.TestCase):
    def setUp(self):
        self.table = EmbeddingTable(dim=10)

    def test_lookup_matches_plain_embed_function(self):
        self.assertEqual(self.table.lookup("cat"), embed("cat", dim=10))

    def test_repeated_lookup_is_cached_and_consistent(self):
        first = self.table.lookup("cat")
        self.assertEqual(len(self.table._cache), 1)
        second = self.table.lookup("cat")
        self.assertEqual(first, second)
        self.assertEqual(len(self.table._cache), 1)

    def test_lookup_is_case_insensitive_via_shared_cache_entry(self):
        self.table.lookup("Cat")
        self.table.lookup("cat")
        self.assertEqual(len(self.table._cache), 1)

    def test_lookup_many_preserves_order_and_repeats(self):
        vectors = self.table.lookup_many(["the", "cat", "the"])
        self.assertEqual(vectors[0], vectors[2])
        self.assertEqual(vectors[0], self.table.lookup("the"))
        self.assertEqual(vectors[1], self.table.lookup("cat"))

    def test_separate_tables_with_same_dim_agree(self):
        other = EmbeddingTable(dim=10)
        self.assertEqual(self.table.lookup("mouse"), other.lookup("mouse"))


if __name__ == "__main__":
    unittest.main()
