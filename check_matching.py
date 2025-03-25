import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from tutorials.models.employer_models import Job, Candidate

# Get the job titled "Soft"
job = Job.objects.filter(title__iexact="Soft").first()

if not job:
    print("❌ No job found with the title 'Soft'.")
else:
    print(f"\n🔍 Job Found: {job.title}")

    # Extract job skills
    job_skills = job.get_extracted_skills()
    if not job_skills:
        print("⚠️ No extracted skills found for this job.")
        job_skills = []

    job_skills_text = " ".join(job_skills).lower()
    print(f"📌 Extracted Job Skills: {job_skills}")

    # Get candidates who applied for this job
    candidates = Candidate.objects.filter(job=job)

    if not candidates.exists():
        print("❌ No candidates applied for this job.")
    else:
        print("\n👥 Candidates Who Applied & Match Scores:")

        candidate_scores = []
        for candidate in candidates:
            print(f"\n🔹 Checking Candidate: {candidate.user.username}")

            try:
                candidate_skills = json.loads(candidate.skills if candidate.skills else "[]")
            except json.JSONDecodeError:
                print(f"❌ Invalid JSON format for {candidate.user.username}, resetting skills.")
                candidate_skills = []
                candidate.skills = "[]"
                candidate.save()

            if not candidate_skills:
                print(f"⚠️ Candidate {candidate.user.username} has no extracted skills.")
                continue

            candidate_skills_text = " ".join(candidate_skills).lower()

            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([job_skills_text, candidate_skills_text])
            similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0]

            print(f"👤 {candidate.user.username} - Match Score: {similarity:.2f}")

            candidate_scores.append((candidate, similarity))

        # Sort candidates by best match score
        candidate_scores.sort(key=lambda x: x[1], reverse=True)

        if candidate_scores:
            print("\n🏆 Top Matches for Job 'Soft':")
            for rank, (candidate, score) in enumerate(candidate_scores, 1):
                print(f"{rank}. {candidate.user.username} - Score: {score:.2f}")
        else:
            print("❌ No suitable candidates found.")

