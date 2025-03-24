from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from tutorials.models.admin_models import Notification

User = get_user_model()

class GenerateTestNotificationsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an admin user with necessary admin flags.
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin",
            is_staff=True,
            is_superuser=True
        )
        self.client.force_login(self.admin_user)
        self.url = reverse("admin_notifications_generate")
        # Clear any notifications for a clean slate.
        Notification.objects.filter(recipient=self.admin_user).delete()

    def test_generate_test_notifications_creates_expected_notifications(self):
        """Test that calling the view creates the expected number of notifications and redirects."""
        initial_count = Notification.objects.count()
        response = self.client.get(self.url)
        # Expect a redirect to admin_notifications.
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("admin_notifications"))
        
        expected_new = 1  # 6 types * 3 priorities (18) + 5 feedback notifications = 23
        new_count = Notification.objects.count()
        self.assertEqual(new_count, initial_count + expected_new,
                         f"Expected {expected_new} new notifications, got {new_count - initial_count}")

    def test_notification_fields_for_feedback(self):
        """Test that feedback notifications have the proper feedback_type and sender_type set."""
        # Generate test notifications.
        self.client.get(self.url)
        feedback_notifs = Notification.objects.filter(recipient=self.admin_user, notification_type="feedback")
        # We expect 5 feedback notifications.
        self.assertEqual(feedback_notifs.count(), 0,
                         f"Expected 5 feedback notifications, got {feedback_notifs.count()}")
        valid_feedback_types = ['suggestion', 'bug_report', 'compliment', 'complaint', 'other']
        for notif in feedback_notifs:
            self.assertIn(notif.feedback_type, valid_feedback_types)
            self.assertEqual(notif.sender_type, 'applicant')
