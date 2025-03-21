import re
from keybert import KeyBERT

kw_model = KeyBERT()

def extract_skills_nlp(text, top_n=20):
    if not text:
        return []

    # Step 1: Extract KeyBERT phrases
    keybert_phrases = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 3),
        stop_words='english',
        top_n=top_n
    )
    keybert_results = [kw[0].lower() for kw in keybert_phrases]

    # Step 2: Use regex to filter meaningful words (no NLTK needed)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text)  # Words with 3+ letters

    # Combine KeyBERT + regex results, remove duplicates
    combined = list(set(keybert_results + words))

    return combined
