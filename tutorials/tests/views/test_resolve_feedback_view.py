import json
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from tutorials.models.admin_models import Notification

User = get_user_model()

class ResolveFeedbackViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an admin user with necessary flags.
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin",
            is_staff=True,
            is_superuser=True
        )
        self.client.force_login(self.admin_user)
        # Create a sample feedback notification.
        self.feedback_notification = Notification.objects.create(
            recipient=self.admin_user,
            title="Feedback Test",
            message="This is a test feedback notification.",
            notification_type="feedback",
            priority="high",  # start with high priority
            is_read=False,
            is_deleted=False,
            created_at=timezone.now()
        )
        # Build URL for resolve_feedback view.
        self.url = reverse("resolve_feedback", kwargs={"feedback_id": self.feedback_notification.id})

    def test_invalid_method_get(self):
        """Test that GET requests are not allowed (405 Method Not Allowed)."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_resolve_feedback_successful(self):
        """Test that a valid POST request resolves the feedback notification."""
        payload = {}  # No additional data needed.
        response = self.client.post(self.url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("status"), "success")
        # Refresh notification from DB.
        self.feedback_notification.refresh_from_db()
        self.assertTrue(self.feedback_notification.is_read)
        self.assertEqual(self.feedback_notification.priority, "low")

    def test_feedback_not_found(self):
        """Test that providing a non-existent feedback_id returns a 404 error."""
        invalid_url = reverse("resolve_feedback", kwargs={"feedback_id": 99999})
        payload = {}
        response = self.client.post(invalid_url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertEqual(data.get("message"), "Feedback not found")

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.post(self.url, data=json.dumps({}), content_type="application/json")
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)
