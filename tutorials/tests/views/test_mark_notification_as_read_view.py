from django.test import TestCase, Client
from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.utils import timezone

from tutorials.models.admin_models import Notification  # Adjust import path if needed
from tutorials.views.admin_views import is_admin  # For reference

User = get_user_model()

class MarkNotificationAsReadViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an admin user with proper flags so that is_admin passes.
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin",
            is_staff=True,
            is_superuser=True
        )
        self.client.force_login(self.admin_user)
        
        # Create a sample notification (unread, not deleted)
        self.notification = Notification.objects.create(
            title="Test Notification",
            message="This is a test notification.",
            notification_type="general",
            priority="medium",
            is_read=False,
            is_deleted=False,
            created_at=timezone.now()
        )
        
        # Construct URL for marking notification as read.
        # Assume URL pattern name is "mark_notification_as_read" and it takes notification_id.
        self.url = reverse("mark_notification_as_read", kwargs={"notification_id": self.notification.id})

    def test_mark_notification_as_read_successful(self):
        """Test that a valid POST request marks the notification as read and returns JSON success."""
        response = self.client.post(self.url)
        # Expect a JSON response with 200 status code.
        self.assertEqual(response.status_code, 200)
        # Parse JSON response.
        json_data = response.json()
        self.assertEqual(json_data.get("status"), "success")
        # Reload the notification from the DB.
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_invalid_method_get(self):
        """Test that a GET request is not allowed (405 Method Not Allowed)."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected."""
        self.client.logout()
        response = self.client.post(self.url)
        # Since the view is protected by @user_passes_test, we expect a redirect to login.
        login_url = reverse("log_in")  # Adjust if your login URL is named differently.
        self.assertEqual(response.status_code, 302)
        self.assertIn(login_url, response.url)
