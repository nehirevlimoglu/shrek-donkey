# tutorials/tests/utils/test_extract_skills_nlp.py

import re
from unittest.mock import patch, MagicMock
from django.test import TestCase

# If extract_skills_nlp and kw_model are in tutorials/utils/__init__.py:
from tutorials.utils import extract_skills_nlp

class ExtractSkillsNLPTest(TestCase):
    def test_empty_text_returns_empty_list(self):
        self.assertEqual(extract_skills_nlp(""), [])
        self.assertEqual(extract_skills_nlp(None), [])

    @patch("tutorials.utils.kw_model")  # ← Update the patch target
    def test_merges_keybert_phrases_and_regex_words(self, mock_kw_model):
        text = "Python developer with AI experience. C++ dev"
        mock_kw_model.extract_keywords.return_value = [
            ("python developer", 0.9),
            ("ai", 0.7),
        ]
        result = extract_skills_nlp(text, top_n=10)

        mock_kw_model.extract_keywords.assert_called_once_with(
            text,
            keyphrase_ngram_range=(1, 3),
            stop_words='english',
            top_n=10
        )
        # Check a few expected merges
        self.assertIn("python developer", result)
        self.assertIn("developer", result)
        self.assertIn("ai", result)

    @patch("tutorials.utils.kw_model")
    def test_no_keybert_phrases_but_regex_words(self, mock_kw_model):
        mock_kw_model.extract_keywords.return_value = []
        text = "Hello I am a data scientist specialized in python."
        result = extract_skills_nlp(text, top_n=5)
        self.assertIn("Hello", result)
        self.assertIn("python", [r.lower() for r in result])

    @patch("tutorials.utils.kw_model")
    def test_only_keybert_phrases_no_regex(self, mock_kw_model):
        mock_kw_model.extract_keywords.return_value = [
            ("java", 0.8),
            ("sql data analysis", 0.6),
        ]
        text = "C# or R"
        result = extract_skills_nlp(text, top_n=3)
        self.assertIn("java", result)
        self.assertIn("sql data analysis", result)

    @patch("tutorials.utils.kw_model")
    def test_top_n_parameter_respected(self, mock_kw_model):
        mock_kw_model.extract_keywords.return_value = []
        _ = extract_skills_nlp("some text", top_n=7)

        mock_kw_model.extract_keywords.assert_called_once_with(
            "some text",
            keyphrase_ngram_range=(1, 3),
            stop_words='english',
            top_n=7
        )
