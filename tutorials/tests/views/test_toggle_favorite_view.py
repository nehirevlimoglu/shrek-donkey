import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from tutorials.models.employer_models import Job
from tutorials.models.applicants_models import Applicant  # Adjust if needed

User = get_user_model()

class ToggleFavoriteViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an applicant user.
        self.user = User.objects.create_user(
            username="applicantuser",
            email="applicant@example.com",
            password="password123",
            role="Applicant"
        )
        self.client.force_login(self.user)
        
        # Create an Applicant profile for this user.
        # Assume Applicant model has a OneToOneField to User and a ManyToManyField 'favorites' for Job.
        self.applicant = Applicant.objects.create(
            user=self.user,
            # Add other required fields as needed.
        )
        
        # Create a Job instance.
        self.job = Job.objects.create(
            title="Software Engineer",
            description="Job description",
            # Add any other required fields.
        )
        
        self.url = reverse("toggle_favorite")
    
    def test_toggle_favorite_add(self):
        """Test that a POST request adds the job to favorites when not already favorited."""
        payload = {"job_id": self.job.id}
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("favorited"))
        # Verify that the job is in the applicant's favorites.
        self.assertIn(self.job, self.applicant.favorites.all())
    
    def test_toggle_favorite_remove(self):
        """Test that a POST request removes the job from favorites when already favorited."""
        # Pre-add the job to favorites.
        self.applicant.favorites.add(self.job)
        payload = {"job_id": self.job.id}
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data.get("favorited"))
        # Verify that the job is no longer in favorites.
        self.assertNotIn(self.job, self.applicant.favorites.all())
    
    def test_job_not_found(self):
        """Test that if the job does not exist, a 404 JSON error is returned."""
        payload = {"job_id": 99999}
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Job not found.")
    
    def test_invalid_request_method(self):
        """Test that a non-POST request returns a 400 error."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Invalid request method.")
    
    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        payload = {"job_id": self.job.id}
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from tutorials.models.employer_models import Job
from tutorials.models.applicants_models import Applicant  # Adjust if needed

User = get_user_model()

class ToggleFavoriteViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an applicant user.
        self.user = User.objects.create_user(
            username="applicantuser",
            email="applicant@example.com",
            password="password123",
            role="Applicant"
        )
        self.client.force_login(self.user)
        
        # Create an Applicant profile for this user.
        # Assume Applicant model has a OneToOneField to User and a ManyToManyField 'favorites' for Job.
        self.applicant = Applicant.objects.create(
            user=self.user,
            # Add other required fields as needed.
        )
        
        # Create a Job instance.
        self.job = Job.objects.create(
            title="Software Engineer",
            description="Job description",
            # Add any other required fields.
        )
        
        self.url = reverse("toggle_favorite")
    
    def test_toggle_favorite_add(self):
        """Test that a POST request adds the job to favorites when not already favorited."""
        payload = {"job_id": self.job.id}
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("favorited"))
        # Verify that the job is in the applicant's favorites.
        self.assertIn(self.job, self.applicant.favorites.all())
    
    def test_toggle_favorite_remove(self):
        """Test that a POST request removes the job from favorites when already favorited."""
        # Pre-add the job to favorites.
        self.applicant.favorites.add(self.job)
        payload = {"job_id": self.job.id}
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data.get("favorited"))
        # Verify that the job is no longer in favorites.
        self.assertNotIn(self.job, self.applicant.favorites.all())
    
    def test_job_not_found(self):
        """Test that if the job does not exist, a 404 JSON error is returned."""
        payload = {"job_id": 99999}
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Job not found.")
    
    def test_invalid_request_method(self):
        """Test that a non-POST request returns a 400 error."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Invalid request method.")
    
    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        payload = {"job_id": self.job.id}
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)
