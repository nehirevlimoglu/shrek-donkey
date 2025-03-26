from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from tutorials.models.admin_models import Notification  # Adjust the import path as needed

User = get_user_model()

class DeleteAllNotificationsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an admin user that passes the is_admin check.
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin",
            is_staff=True,
            is_superuser=True
        )
        self.client.force_login(self.admin_user)
        
        # Create several notifications that are not deleted.
        self.notifications = []
        for i in range(5):
            notif = Notification.objects.create(
                title=f"Notification {i+1}",
                message="Test message",
                recipient=self.admin_user,  # ✅ important for filtering correctly
                notification_type="general",
                priority="medium",
                is_read=False,
                is_deleted=False,
                created_at=timezone.now()
            )
            self.notifications.append(notif)
        
        # URL for the view (updated name)
        self.url = reverse("clear_all_notifications")

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected."""
        self.client.logout()
        response = self.client.post(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)

    def test_invalid_method_get(self):
        """Test that GET request is not allowed (405 Method Not Allowed)."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_delete_all_notifications_successful(self):
        """Test that a valid POST request soft deletes all notifications and returns JSON success."""
        # Before POST, ensure notifications are not deleted.
        active_count = Notification.objects.filter(is_deleted=False, recipient=self.admin_user).count()
        self.assertEqual(active_count, 5)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        
        json_data = response.json()
        self.assertTrue(json_data.get("success"))

        # Verify that all notifications are now marked as deleted.
        remaining = Notification.objects.filter(is_deleted=False, recipient=self.admin_user).count()
        self.assertEqual(remaining, 0)
