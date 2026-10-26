import unittest

from attentionlive.tokenize import tokenize


class TokenizeTests(unittest.TestCase):
    def test_splits_words(self):
        self.assertEqual(tokenize("the cat sat"), ["the", "cat", "sat"])

    def test_keeps_punctuation_as_separate_tokens(self):
        self.assertEqual(tokenize("hi, there!"), ["hi", ",", "there", "!"])

    def test_empty_string_yields_no_tokens(self):
        self.assertEqual(tokenize(""), [])


if __name__ == "__main__":
    unittest.main()
