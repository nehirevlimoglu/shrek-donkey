# jobs/utils.py

import nltk
from keybert import KeyBERT
from nltk import word_tokenize, pos_tag

# Auto-download
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

kw_model = KeyBERT()

def extract_skills_nlp(text, top_n=20):
    if not text:
        return []

    keywords = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 3),  # (1, 3) includes 1-word, 2-word, and 3-word phrases
        stop_words='english',
        top_n=top_n
    )

    return [kw[0] for kw in keywords]
