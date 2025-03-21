import re
import json
from keybert import KeyBERT
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from tutorials.models.employer_models import Job, Candidate  # Adjust if needed

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


def match_candidates_to_job(job_title, top_n=5):
    """Finds the best candidates for a given job based on extracted skills similarity."""

    job = Job.objects.filter(title__iexact=job_title).first()
    if not job:
        return f"❌ No job found with the title '{job_title}'."
    
    job_skills = job.get_extracted_skills()
    if not job_skills:
        return "⚠️ No extracted skills found for this job."
    
    job_skills_text = " ".join(job_skills).lower()

    candidates = Candidate.objects.filter(job=job)
    if not candidates.exists():
        return "❌ No candidates applied for this job."

    candidate_scores = []
    
    for candidate in candidates:
        print(f"🔍 Checking candidate: {candidate.user.username}")
        print(f"📌 Raw skills field: {repr(candidate.skills)}")  # Debugging print

        candidate_skills = candidate.skills  # Get raw value

        if not candidate_skills or candidate_skills.strip() == "":
            print("⚠️ Candidate skills are empty, setting to []")
            candidate_skills = "[]"  # Force a valid empty list format

        try:
            candidate_skills = json.loads(candidate_skills)  # Attempt JSON decoding
        except json.JSONDecodeError:
            print(f"❌ Error decoding JSON for {candidate.user.username}, resetting skills.")
            candidate_skills = []  # If error, set to empty list

        if not candidate_skills:
            continue  # Skip if no skills extracted

        candidate_skills_text = " ".join(candidate_skills).lower()

        vectorizer = TfidfVectorizer()
        tfidf_matrix = vectorizer.fit_transform([job_skills_text, candidate_skills_text])
        similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]

        candidate_scores.append((candidate, similarity))


    candidate_scores.sort(key=lambda x: x[1], reverse=True)

    return candidate_scores[:top_n]