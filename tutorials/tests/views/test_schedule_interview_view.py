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

class ScheduleInterviewViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()

        # Create an applicant user.
        self.applicant_user = User.objects.create_user(
            username="applicantuser",
            email="applicant@example.com",
            password="password123",
            role="Applicant"
        )
        self.client.force_login(self.applicant_user)

        # Create an Applicant profile for the applicant user.
        self.applicant_obj = Applicant.objects.create(
            user=self.applicant_user,
            # Add other required fields as necessary.
        )

        # Create an employer and job (needed for the application/interview).
        self.employer_user = User.objects.create_user(
            username="employeruser",
            email="employer@example.com",
            password="password123",
            role="Employer"
        )
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username="employeruser",  # Must match if needed in views
            email="employer@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )
        self.job = Job.objects.create(
            employer=self.employer,
            title="Software Engineer",
            description="Job description",
            application_deadline=self.today + datetime.timedelta(days=10)
        )

        # Create a Candidate instance for the interview.
        self.candidate = Candidate.objects.create(
            user=self.applicant_user,
            job=self.job,
            application_status="under_review",
            application_date=timezone.now(),
            first_name="John",
            last_name="Doe"
        )

        # Build the URL for schedule_interview view using the candidate's id.
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
        # Prepare valid form data.
        interview_date = (self.today + datetime.timedelta(days=1)).isoformat()  # e.g. "2025-03-24"
        interview_time = "10:30:00"
        interview_link = "http://example.com/interview"
        notes = "Please prepare for technical questions."

        data = {
            "interview_date": interview_date,
            "interview_time": interview_time,
            "interview_link": interview_link,
            "notes": notes,
        }
        response = self.client.post(self.url, data)
        # Expect a redirect to 'employer_calendar'
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("employer_calendar"))
        # Check that an Interview was created for the candidate and the job.
        interview = Interview.objects.filter(candidate=self.candidate, job=self.job).first()
        self.assertIsNotNone(interview)
        self.assertEqual(interview.interview_link, interview_link)
        # Check that an ApplicantNotification was created for the applicant.
        notification = ApplicantNotification.objects.filter(applicant=self.applicant_obj, title__icontains="Interview Scheduled").first()
        self.assertIsNotNone(notification)
        # Check that a success message was added.
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Interview scheduled successfully!" in message.message for message in messages))

    def test_post_invalid_date_time(self):
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
        response = self.client.post(self.url, data)
        # Expect redirect regardless.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("employer_calendar"))
        # Interview should be created.
        interview = Interview.objects.filter(candidate=self.candidate, job=self.job).first()
        self.assertIsNotNone(interview)
        # No ApplicantNotification should be created for this applicant.
        notifications = self.applicant_obj.notifications.all() if hasattr(self.applicant_obj, "notifications") else []
        self.assertEqual(notifications.count(), 0)
