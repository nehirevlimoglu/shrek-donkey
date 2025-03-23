import re
import json
from keybert import KeyBERT
from sentence_transformers import SentenceTransformer, util
from tutorials.models.employer_models import Job, Candidate  # Adjust if needed

kw_model = KeyBERT()
semantic_model = SentenceTransformer('all-MiniLM-L6-v2')  # Fast & good

# 🔸 Soft skills list for penalty logic
SOFT_SKILLS = {
    "teamwork", "communication", "communicator", "empathy", "empathic",
    "hardworking", "collaboration", "collaborative", "adaptability", "adaptable",
    "passionate", "motivated", "creative", "creativity", "leadership", "leader",
    "problem solving", "problem-solver", "dedicated", "responsible",
    "organized", "organization", "punctual", "flexible", "flexibility",
    "attention to detail", "multi-tasking", "initiative", "positive attitude",
    "interpersonal skills", "self-starter", "fast learner", "work ethic",
    "time management", "reliable", "independent", "detail-oriented",
    "good listener", "critical thinking", "curious", "driven", "team player"
}

SOFT_SKILL_PENALTY_THRESHOLD = 0.75  # ≥50% soft skills
SOFT_SKILL_PENALTY_FACTOR = 0.85    # Reduce score by 15% if soft-skills-heavy

def extract_skills_nlp(text, top_n=20):
    if not text:
        return []
    # Ensure text is a string
    if not isinstance(text, str):
        text = str(text)

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
    """Finds the best candidates for a given job based on semantic skill similarity, 
       work experience, discipline matching, and a minimum match threshold.
    """
    MIN_MATCH_THRESHOLD = 0.68  # Any score below this is not considered a match
    
    job = Job.objects.filter(title__iexact=job_title).first()
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
        if raw_skills is None:
            print(f"⚠️ No skills found for {candidate.user.username}, skipping.")
            continue
        # Ensure raw_skills is a string
        if not isinstance(raw_skills, str):
            raw_skills = str(raw_skills)
        if raw_skills.strip() == "":
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
        
        # Apply soft skills penalty if needed
        soft_count = sum(1 for skill in candidate_skills if skill.lower() in SOFT_SKILLS)
        ratio = soft_count / len(candidate_skills)
        if ratio >= SOFT_SKILL_PENALTY_THRESHOLD:
            print(f"⚠️ Soft skill ratio too high for {candidate.user.username} ({ratio:.2f}), applying penalty.")
            similarity *= SOFT_SKILL_PENALTY_FACTOR
        
        # Incorporate work experience into the matching score if job has a requirement
        if job.required_experience is not None:
            candidate_experience = candidate.total_experience_years
            if candidate_experience < job.required_experience:
                similarity *= (candidate_experience / job.required_experience)
                print(f"⚠️ {candidate.user.username}'s experience ({candidate_experience:.2f} years) is below the required {job.required_experience} years. Adjusted similarity: {similarity:.4f}")
        
        # Discipline matching if the job has a discipline requirement
        if job.required_discipline:
            candidate_discipline = candidate.discipline.lower() if candidate.discipline else ""
            required_discipline = job.required_discipline.lower()
            
            if candidate_discipline != required_discipline:
                # Apply a penalty if they don't match
                similarity *= 0.5
                print(f"⚠️ {candidate.user.username}'s discipline ({candidate_discipline}) does not match the required discipline ({required_discipline}). Adjusted similarity: {similarity:.4f}")
            else:
                # Slight bonus if they match exactly
                similarity *= 1.05
                print(f"✅ {candidate.user.username}'s discipline matches the required discipline. Adjusted similarity: {similarity:.4f}")

        candidate_scores.append((candidate, similarity))
    
    # Sort candidates by similarity descending
    candidate_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Filter out candidates whose score is below the threshold
    filtered_scores = [(cand, score) for cand, score in candidate_scores if score >= MIN_MATCH_THRESHOLD]
    
    # Return the top N from the filtered list
    return filtered_scores[:top_n]
