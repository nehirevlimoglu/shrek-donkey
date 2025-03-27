# tutorials/tests/forms/test_employer_reschedule_interview_form.py

from django.test import TestCase
from tutorials.forms.employer_forms import RescheduleInterviewForm
from tutorials.models.employer_models import Interview, Job, Candidate
from django.contrib.auth import get_user_model
from datetime import date, time
from django.utils import timezone

User = get_user_model()

class RescheduleInterviewFormTest(TestCase):

    def setUp(self):
        """Set up a dummy interview with candidate and job."""
        # Create a test user.
        self.user = User.objects.create_user(username="jj", email="jj@test.com", password="1234")
        
        # Create a Candidate instance for this user.
        self.candidate = Candidate.objects.create(user=self.user)
        
        # Create a Job instance.
        # Removed the 'position' keyword since it is not defined on the Job model.
        self.job = Job.objects.create(
            title="Test Job",
            company_name="TestCo",
            location="Remote",
            job_type="Full Time",
            salary="80000",
            description="Testing things",
            requirements="None",
            benefits="None",
            application_deadline="2025-12-31",
            contact_email="hr@test.com"
        )

        # Create an Interview instance.
        self.interview = Interview.objects.create(
            candidate=self.candidate,
            job=self.job,
            date="2025-04-01",
            time="09:00",
            interview_link="https://zoom.us/old-link",
            notes="Initial schedule"
        )

    def test_valid_form_data(self):
        """Form should validate and update interview details."""
        form_data = {
            "date": "2025-04-05",
            "time": "11:00",
            "interview_link": "https://zoom.us/new-link",
            "notes": "Rescheduled due to conflict"
        }
        form = RescheduleInterviewForm(data=form_data, instance=self.interview)
        self.assertTrue(form.is_valid(), form.errors)
        updated = form.save()
        self.assertEqual(updated.date, date(2025, 4, 5))
        self.assertEqual(updated.time, time(11, 0))
        self.assertEqual(updated.interview_link, "https://zoom.us/new-link")
        self.assertEqual(updated.notes, "Rescheduled due to conflict")

    def test_invalid_time_format(self):
        """Invalid time string should fail validation."""
        form_data = {
            "date": "2025-04-05",
            "time": "not-a-time",
            "interview_link": "https://zoom.us/new-link",
            "notes": "Testing time error"
        }
        form = RescheduleInterviewForm(data=form_data, instance=self.interview)
        self.assertFalse(form.is_valid())
        self.assertIn("time", form.errors)

    def test_missing_required_fields(self):
        """Missing required fields like date/time should error."""
        form_data = {
            "date": "",  # Missing
            "time": "",  # Missing
            "interview_link": "https://zoom.us/new-link",
            "notes": ""
        }
        form = RescheduleInterviewForm(data=form_data, instance=self.interview)
        self.assertFalse(form.is_valid())
        self.assertIn("date", form.errors)
        self.assertIn("time", form.errors)
