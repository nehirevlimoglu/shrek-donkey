from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from tutorials.models.employer_models import Employer, EmployerEvent

User = get_user_model()

class GetEmployerEventsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an employer user.
        self.employer_user = User.objects.create_user(
            username="employeruser",
            email="employer@example.com",
            password="password123",
            role="Employer"
        )
        self.client.force_login(self.employer_user)
        # Create an Employer instance with the same username.
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username="employeruser",  # must match request.user.username
            email="employer@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )
        # Create two EmployerEvent instances for this employer.
        self.event1 = EmployerEvent.objects.create(
            employer=self.employer,
            title="Event 1",
            start=timezone.now(),
            end=timezone.now() + timezone.timedelta(hours=1)
        )
        self.event2 = EmployerEvent.objects.create(
            employer=self.employer,
            title="Event 2",
            start=timezone.now() + timezone.timedelta(days=1),
            end=None
        )
        self.url = reverse("get_employer_events")

    def test_get_employer_events_success(self):
        """Test that a logged-in employer receives a JSON list of events with the expected fields."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # Parse the JSON response.
        event_list = response.json()
        self.assertIsInstance(event_list, list)
        # We expect two events.
        self.assertEqual(len(event_list), 2)
        # Check structure of first event.
        event = event_list[0]
        self.assertIn("id", event)
        self.assertIn("title", event)
        self.assertIn("start", event)
        self.assertIn("end", event)
        # Verify that the start field is in ISO format with a 'T'.
        self.assertIn("T", event["start"])
        # For event2, end should be None.
        for ev in event_list:
            if ev["id"] == self.event2.id:
                self.assertIsNone(ev["end"])

    def test_employer_not_found(self):
        """Test that if the logged-in user does not have an Employer profile, a JSON error is returned with status 403."""
        # Create a user with role Employer but do NOT create an Employer instance.
        user_without_employer = User.objects.create_user(
            username="nouseremployer",
            email="nouseremployer@example.com",
            password="password123",
            role="Employer"
        )
        self.client.force_login(user_without_employer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Employer not found")

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)
