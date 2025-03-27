from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

# Import your Notification model. Adjust the import path if needed.
from tutorials.models.admin_models import Notification
# Also import your admin check function if needed.
from tutorials.views.admin_views import is_admin

User = get_user_model()

class MarkAllNotificationsAsReadViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an admin user with proper flags to pass is_admin check.
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin",
            is_staff=True,
            is_superuser=True
        )
        self.client.force_login(self.admin_user)
        
        # Create several notifications.
        # We'll create 4 unread notifications.
        self.notifications = []
        for i in range(4):
            notif = Notification.objects.create(
                recipient=self.admin_user,  # ← FIX: associate with the logged-in admin
                title=f"Notification {i+1}",
                message="Test message",
                notification_type="general",
                priority="medium",
                is_read=False,
                is_deleted=False,
                created_at=timezone.now()
            )
            self.notifications.append(notif)
        
        # Also create one notification that's already read, to ensure it remains read.
        Notification.objects.create(
            recipient=self.admin_user,  # ← also assign recipient here
            title="Notification Read",
            message="Already read message",
            notification_type="general",
            priority="medium",
            is_read=True,
            is_deleted=False,
            created_at=timezone.now()
        )

        
        # Get URL for mark_all_notifications_as_read view.
        self.url = reverse("mark_all_notifications_as_read")
        
    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.post(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)
        
    def test_invalid_method_get(self):
        """Test that GET requests are not allowed (405 Method Not Allowed)."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        
    def test_mark_all_notifications_as_read_successful(self):
        """Test that a POST request marks all unread notifications as read and returns JSON success."""
        # Check initial unread count.
        initial_unread = Notification.objects.filter(is_read=False, is_deleted=False).count()
        self.assertEqual(initial_unread, 4)
        
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        
        json_data = response.json()
        self.assertIn("success", json_data)
        self.assertTrue(json_data["success"])

        
        # Verify that all unread notifications are now marked as read.
        final_unread = Notification.objects.filter(is_read=False, is_deleted=False).count()
        self.assertEqual(final_unread, 0)
