import re
import json
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer, util
from tutorials.models.employer_models import Job, Candidate  # Adjust if needed

kw_model = KeyBERT()
semantic_model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast & good

def extract_skills_nlp(text, top_n=20):
    if not text:
        return []

    keybert_phrases = kw_model.extract_keywords(
        text,
        keyphrase_ngram_range=(1, 3),
        stop_words='english',
        top_n=top_n
    )
    keybert_results = [kw[0].lower() for kw in keybert_phrases]

    words = re.findall(r'\b[a-zA-Z]{3,}\b', text)  # Words with 3+ letters

    combined = list(set(keybert_results + words))
    return combined

def match_candidates_to_job(job_title, top_n=5):
    """Finds the best candidates for a given job based on semantic skill similarity."""


    job = Job.objects.filter(title__iexact=job_title).first()
    print("🧠 DEBUG - Job Requirements Text:", job.requirements)
    print("🧠 DEBUG - Extracted Job Skills:", job.get_extracted_skills())
    
    if not job:
        return f"❌ No job found with the title '{job_title}'."
    
    job_skills = job.get_extracted_skills()
    if not job_skills:
        return "⚠️ No extracted skills found for this job."
    
    job_skills_text = " ".join(job_skills).lower()
    job_vector = semantic_model.encode(job_skills_text, convert_to_tensor=True)

    candidates = Candidate.objects.filter(job=job)
    if not candidates.exists():
        return "❌ No candidates applied for this job."

    candidate_scores = []

    for candidate in candidates:
        print(f"🔍 Checking candidate: {candidate.user.username}")
        print(f"📌 Raw skills field: {repr(candidate.skills)}")

        raw_skills = candidate.skills

        if not raw_skills or raw_skills.strip() == "":
            print(f"⚠️ No skills found for {candidate.user.username}, skipping.")
            continue

        try:
            skill_data = json.loads(raw_skills)
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON for {candidate.user.username}, falling back to raw string.")
            skill_data = raw_skills

        if isinstance(skill_data, list):
            raw_text = " ".join(skill_data)
        else:
            raw_text = skill_data

        candidate_skills = extract_skills_nlp(raw_text)
        if not candidate_skills:
            continue

        candidate_skills_text = " ".join(candidate_skills).lower()
        cand_vector = semantic_model.encode(candidate_skills_text, convert_to_tensor=True)

        similarity = util.pytorch_cos_sim(job_vector, cand_vector).item()
        candidate_scores.append((candidate, similarity))

    candidate_scores.sort(key=lambda x: x[1], reverse=True)
    return candidate_scores[:top_n]  # This is already returning (candidate, score) pairs

