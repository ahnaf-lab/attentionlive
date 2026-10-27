import unittest

from attentionlive.tokenize import tokenize


class TokenizeTests(unittest.TestCase):
    def test_splits_words(self):
        self.assertEqual(tokenize("the cat sat"), ["the", "cat", "sat"])

    def test_keeps_punctuation_as_separate_tokens(self):
        self.assertEqual(tokenize("hi, there!"), ["hi", ",", "there", "!"])

    def test_empty_string_yields_no_tokens(self):
        self.assertEqual(tokenize(""), [])

    def test_keeps_hyphenated_and_apostrophe_words_whole(self):
        self.assertEqual(
            tokenize("well-known, don't go"),
            ["well-known", ",", "don't", "go"],
        )

    def test_handles_unicode_letters(self):
        self.assertEqual(tokenize("café résumé"), ["café", "résumé"])

    def test_no_character_is_silently_dropped(self):
        tokens = tokenize("a@b (c)")
        self.assertEqual(tokens, ["a", "@", "b", "(", "c", ")"])


if __name__ == "__main__":
    unittest.main()
