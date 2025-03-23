from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from tutorials.models.employer_models import Job, Candidate
from django.contrib.auth import get_user_model

User = get_user_model()

class JobMatchingViewTests(TestCase):

    def setUp(self):
        self.client = Client()

        self.job = Job.objects.create(
            title="Python Developer",
            requirements="Experience in Python, Django, REST APIs."
        )

        self.matching_url = reverse('match_candidates', args=[self.job.id])

    @patch('tutorials.views.views.match_candidates_to_job')
    def test_job_matching_view_successful(self, mock_match):
        """Test the view successfully returns matched candidates."""
        mock_candidate = Candidate()
        mock_candidate.user = User(username="@testuser")

        mock_match.return_value = [(mock_candidate, 0.95)]

        response = self.client.get(self.matching_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "candidate_matches.html")
        self.assertIn("matched_candidates", response.context)
        self.assertEqual(response.context["matched_candidates"], [(mock_candidate, 0.95)])

    @patch('tutorials.views.views.match_candidates_to_job')
    def test_job_matching_view_error_string(self, mock_match):
        """Test the view handles an error string from the matching function gracefully."""

        mock_match.return_value = "⚠️ No candidates applied for this job."

        response = self.client.get(self.matching_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "candidate_matches.html")
        self.assertIn("error", response.context)
        self.assertEqual(response.context["error"], "⚠️ No candidates applied for this job.")

    def test_job_matching_view_invalid_job(self):
        """Test the view returns 404 for invalid job id."""

        invalid_url = reverse('match_candidates', args=[9999])

        response = self.client.get(invalid_url)

        self.assertEqual(response.status_code, 404)

    @patch('tutorials.views.views.match_candidates_to_job')
    def test_job_matching_view_no_candidates(self, mock_match):
        """Test the view correctly displays a message when no matches found."""

        mock_match.return_value = []

        response = self.client.get(self.matching_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "candidate_matches.html")
        self.assertIn("matched_candidates", response.context)
        self.assertEqual(response.context["matched_candidates"], [])