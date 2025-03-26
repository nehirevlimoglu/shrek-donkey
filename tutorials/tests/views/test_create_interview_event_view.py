from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from tutorials.models.employe_models import Calendar, Event  # or adjust import path if you're using custom models
from tutorials.models.employer_models import Candidate, Job

User = get_user_model()

class CreateInterviewEventViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "testpass123"
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password=self.password
        )
        self.client.login(username="testuser", password=self.password)

        # Setup a job and candidate with id=1 (hardcoded in view)
        self.job = Job.objects.create(
            title="Software Engineer",
            description="Test job",
            application_deadline=timezone.now().date() + timedelta(days=7)
        )
        self.candidate = Candidate.objects.create(
            user=self.user,
            job=self.job,
            first_name="John",
            last_name="Doe",
            application_status="Pending"
        )
        self.url = reverse("create_interview_event")  # adjust if needed

    def test_interview_event_created_and_redirects(self):
        """Test that the view creates an Event and redirects properly."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("schedule"))

        # Confirm that the event was created
        event = Event.objects.latest("start")
        self.assertEqual(event.title, f"Interview - {self.candidate.user.first_name} (Software Engineer)")
        self.assertEqual(event.creator, self.user)

        # Check calendar association
        self.assertEqual(event.calendar.slug, "interviews")

    def test_calendar_created_if_missing(self):
        """Test that a new 'interviews' calendar is created if it does not exist."""
        Calendar.objects.all().delete()  # Ensure no calendar exists
        self.client.get(self.url)
        self.assertTrue(Calendar.objects.filter(slug="interviews").exists())

    def test_event_times_are_set_for_tomorrow(self):
        """Ensure the event is scheduled for 10am–11am tomorrow."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        event = Event.objects.latest("start")
        tomorrow = timezone.now().date() + timedelta(days=1)
        self.assertEqual(event.start.date(), tomorrow)
        self.assertEqual(event.start.hour, 10)
        self.assertEqual(event.end.hour, 11)
