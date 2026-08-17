import unittest

from quant_update_bot.text_match import contains_keyword


class TextMatchTests(unittest.TestCase):
    def test_matches_words_and_phrases_case_insensitively(self) -> None:
        text = "Factor investing with an ORDER BOOK"
        self.assertTrue(contains_keyword(text, "factor"))
        self.assertTrue(contains_keyword(text, "order book"))

    def test_does_not_match_inside_a_larger_word(self) -> None:
        self.assertFalse(contains_keyword("A riskless benchmark", "risk"))


if __name__ == "__main__":
    unittest.main()
