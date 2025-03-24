from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from tutorials.models.admin_models import Notification  # Adjust import if necessary

User = get_user_model()

class DeleteNotificationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an admin user that passes the is_admin test.
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin",
            is_staff=True,
            is_superuser=True
        )
        # Force login as the admin user.
        self.client.force_login(self.admin_user)
        
        # Create a sample notification (not deleted yet).
        self.notification = Notification.objects.create(
            title="Test Notification",
            message="This is a test notification.",
            notification_type="general",
            priority="medium",
            is_read=False,
            is_deleted=False,
            created_at=timezone.now()
        )
        
        # Construct the URL for delete_notification view using its URL name.
        self.url = reverse("delete_notification", kwargs={"notification_id": self.notification.id})
    
    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.post(self.url)
        # Assuming your login URL is named 'log_in'
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)
    
    def test_invalid_method_get(self):
        """Test that a GET request returns 405 Method Not Allowed."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
    
    def test_delete_notification_successful(self):
        """Test that a valid POST request marks the notification as deleted and returns JSON success."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertEqual(json_data.get("status"), "success")
        # Refresh from database and check that is_deleted is now True.
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_deleted)
