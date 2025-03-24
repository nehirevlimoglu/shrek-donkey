import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.utils.dateparse import parse_date, parse_time

# Import models.
from tutorials.models.employer_models import Employer, Job, Interview, Candidate
from tutorials.models.applicants_models import Applicant, ApplicantNotification  # Adjust if needed

User = get_user_model()

import json
import datetime
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from unittest.mock import patch

from tutorials.models.employer_models import Employer, Job, Interview, Candidate
from tutorials.models.applicants_models import Applicant, ApplicantNotification
from tutorials.forms.applicants_forms import ApplicationForm

User = get_user_model()

User = get_user_model()

class ScheduleInterviewViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()
        
        # Create an employer user (logged in).
        self.employer_user = User.objects.create_user(
            username="employeruser",
            email="employer@example.com",
            password="password123",
            role="Employer"
        )
        self.client.force_login(self.employer_user)
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username="employeruser",
            email="employer@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )
        
        # Create an applicant user (different from the employer) and its profile.
        self.applicant_user = User.objects.create_user(
            username="applicantuser",
            email="applicant@example.com",
            password="password123",
            role="Applicant"
        )
        self.applicant_obj = Applicant.objects.create(user=self.applicant_user)
        
        # Create a Job posted by the employer.
        self.job = Job.objects.create(
            employer=self.employer,
            title="Software Engineer",
            description="Job description",
            application_deadline=self.today + datetime.timedelta(days=10)
        )
        
        # Create a Candidate for the applicant.
        self.candidate = Candidate.objects.create(
            user=self.applicant_user,
            job=self.job,
            application_status="under_review",
            application_date=timezone.now(),
            first_name="John",
            last_name="Doe"
        )
        
        # Build the URL for schedule_interview view using candidate id.
        self.url = reverse("schedule_interview", kwargs={"applicant_id": self.candidate.id})
    
    
    def test_get_schedule_interview_view_success(self):
        """Test that a GET request returns the schedule interview form with the candidate in context."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "schedule_interview.html")
        self.assertIn("applicant", response.context)
        self.assertEqual(response.context["applicant"].id, self.candidate.id)
    
    def test_get_schedule_interview_view_candidate_not_found(self):
        """Test that if the candidate does not exist, a 404 response is returned."""
        invalid_url = reverse("schedule_interview", kwargs={"applicant_id": 99999})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)
        self.assertIn("Candidate does not exist.", response.content.decode())
    
    def test_post_valid_schedule_interview(self):
        """Test that a valid POST request creates an Interview and an ApplicantNotification, then redirects to employer_calendar."""
        interview_date = (self.today + datetime.timedelta(days=1)).isoformat()  # e.g., "2025-03-24"
        interview_time = "10:30:00"
        interview_link = "http://example.com/interview"
        notes = "Please prepare for technical questions."
        
        data = {
            "interview_date": interview_date,
            "interview_time": interview_time,
            "interview_link": interview_link,
            "notes": notes,
        }
        # Use follow=True to follow the redirect chain.
        response = self.client.post(self.url, data, follow=True)
        # The final URL should be employer_calendar.
        final_url = reverse("employer_calendar")
        self.assertEqual(response.redirect_chain[-1][0], final_url)
        self.assertEqual(response.status_code, 200)
        
        # Verify that an Interview was created.
        interview = Interview.objects.filter(candidate=self.candidate, job=self.job).first()
        self.assertIsNotNone(interview)
        self.assertEqual(interview.interview_link, interview_link)
        
        # Verify that an ApplicantNotification was created for the applicant.
        notification = ApplicantNotification.objects.filter(applicant=self.applicant_obj, title__icontains="Interview Scheduled").first()
        self.assertIsNotNone(notification)
        
        # Check that a success message was added.
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Interview scheduled successfully!" in m.message for m in messages))
    
    @patch("tutorials.views.employer_views.parse_date", side_effect=ValueError("Invalid date"))
    @patch("tutorials.views.employer_views.parse_time", side_effect=ValueError("Invalid time"))
    def test_post_invalid_date_time(self, mock_parse_time, mock_parse_date):
        """Test that a POST with an invalid date or time format returns a 400 error."""
        data = {
            "interview_date": "invalid-date",
            "interview_time": "invalid-time",
            "interview_link": "http://example.com/interview",
            "notes": "Some notes",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid date or time format.", response.content.decode())
    
    def test_post_applicant_notification_failure(self):
        """Test that if the Applicant profile does not exist, the interview is still created, but no notification is made."""
        # Delete the Applicant profile.
        self.applicant_obj.delete()
        interview_date = (self.today + datetime.timedelta(days=1)).isoformat()
        interview_time = "10:30:00"
        data = {
            "interview_date": interview_date,
            "interview_time": interview_time,
            "interview_link": "http://example.com/interview",
            "notes": "Notes",
        }
        response = self.client.post(self.url, data, follow=True)
        final_url = reverse("employer_calendar")
        self.assertEqual(response.redirect_chain[-1][0], final_url)
        interview = Interview.objects.filter(candidate=self.candidate, job=self.job).first()
        self.assertIsNotNone(interview)
        # Since the Applicant profile was deleted, no ApplicantNotification should be created.
        notifications = ApplicantNotification.objects.filter(applicant__user=self.candidate.user)
        self.assertEqual(notifications.count(), 0)
    
    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)