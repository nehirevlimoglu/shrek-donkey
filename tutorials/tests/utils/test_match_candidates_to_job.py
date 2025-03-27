import torch
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from tutorials.models.employer_models import Job, Candidate
from tutorials.utils import match_candidates_to_job  # Adjust import if needed

User = get_user_model()

class MatchCandidatesToJobTests(TestCase):
    def setUp(self):
        # Create applicant users for candidates.
        self.user1 = User.objects.create_user(username="@johndoe", password="pass123", email="john@example.com", role="Applicant")
        self.user2 = User.objects.create_user(username="@janedoe", password="pass123", email="jane@example.com", role="Applicant")
        self.user3 = User.objects.create_user(username="@user3", password="pass123", email="user3@example.com", role="Applicant")
        # Create a job with requirements.
        self.job = Job.objects.create(
            title="Junior Developer",
            requirements="We need Python, Django, AI knowledge.",
            required_experience=5,          # Requires 5 years of experience.
            required_discipline="computer science"
        )

    @patch("tutorials.utils.extract_skills_nlp", return_value=["python", "django", "machine learning"])
    @patch("tutorials.utils.util.pytorch_cos_sim")
    @patch("tutorials.utils.semantic_model.encode")
    @patch("tutorials.utils.Job.get_extracted_skills", return_value=["python", "django", "ml"])
    def test_experience_and_discipline_adjustments(
        self, mock_job_skills, mock_encode, mock_cos_sim, mock_extract_skills
    ):
        """
        Tests adjustments due to job.required_experience and job.required_discipline.
        We override the MIN_MATCH_THRESHOLD to 0.25 so that our candidates pass.
        """
        # Temporarily override MIN_MATCH_THRESHOLD in the function's globals.
        original_threshold = match_candidates_to_job.__globals__.get("MIN_MATCH_THRESHOLD", None)
        match_candidates_to_job.__globals__["MIN_MATCH_THRESHOLD"] = 0.25

        # Ensure the job's requirements are set.
        self.job.required_experience = 5
        self.job.required_discipline = "computer science"
        self.job.save()

        # Set up mocks: simulate base similarities.
        mock_encode.side_effect = [
            "JOB_VECTOR",       # For the job.
            "CANDIDATE1_VECTOR",# For candidate 1.
            "CANDIDATE2_VECTOR",# For candidate 2.
            "CANDIDATE3_VECTOR",# For candidate 3.
        ]
        mock_cos_sim.side_effect = [
            torch.tensor([[0.9]]),
            torch.tensor([[0.8]]),
            torch.tensor([[0.7]]),
        ]

        # Create three candidates.
        # Candidate 1: expected final similarity = 0.9 * (3/5) * 0.5 = 0.27.
        cand1 = Candidate.objects.create(
            user=self.user1,
            job=self.job,
            skills='["python", "django"]',
            discipline="IT"  # Mismatch.
        )
        # Bypass property setter by directly injecting into __dict__
        cand1.__dict__['total_experience_years'] = 3

        # Candidate 2: expected final similarity = 0.8 * (5/5) * 0.5 = 0.8 * 0.5 = 0.4.
        cand2 = Candidate.objects.create(
            user=self.user2,
            job=self.job,
            skills='["excel", "office"]',
            discipline="IT"  # Mismatch.
        )
        cand2.__dict__['total_experience_years'] = 5

        # Candidate 3: expected final similarity = 0.7 * (4/5) * 1.05 ≈ 0.588.
        cand3 = Candidate.objects.create(
            user=self.user3,
            job=self.job,
            skills='["python", "django"]',
            discipline="Computer Science"  # Match.
        )
        cand3.__dict__['total_experience_years'] = 4

        # Call the matching function.
        results = match_candidates_to_job("Junior Developer", top_n=5)

        # Restore the original threshold.
        if original_threshold is not None:
            match_candidates_to_job.__globals__["MIN_MATCH_THRESHOLD"] = original_threshold

        # Verify we got all 3 candidates.
        self.assertEqual(len(results), 3, "Should return all 3 candidates in descending order")

        # Expected calculations:
        # Candidate 1: 0.9 * (3/5) = 0.9 * 0.6 = 0.54; discipline penalty: 0.54 * 0.5 = 0.27.
        # Candidate 2: 0.8 * (5/5) = 0.8; discipline penalty: 0.8 * 0.5 = 0.4.
        # Candidate 3: 0.7 * (4/5) = 0.7 * 0.8 = 0.56; discipline match bonus: 0.56 * 1.05 ≈ 0.588.
        # Expected ordering: cand3 (0.588) > cand2 (0.4) > cand1 (0.27).
        self.assertEqual(results[0][0], cand3)
        self.assertAlmostEqual(results[0][1], 0.588, places=3)
        self.assertEqual(results[1][0], cand2)
        self.assertAlmostEqual(results[1][1], 0.4, places=3)
        self.assertEqual(results[2][0], cand1)
        self.assertAlmostEqual(results[2][1], 0.27, places=3)
