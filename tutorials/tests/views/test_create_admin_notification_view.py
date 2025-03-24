from django.test import TestCase
from django.contrib.auth import get_user_model
from tutorials.models.admin_models import Notification
# Adjust the import path as needed:
from tutorials.views.admin_views import create_admin_notification

User = get_user_model()

class CreateAdminNotificationTests(TestCase):

    def setUp(self):
        # Clear any existing notifications for a clean test.
        Notification.objects.all().delete()

        # Create an admin user.
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin",
            is_staff=True,
            is_superuser=True
        )
        # Create a non-admin user.
        self.non_admin_user = User.objects.create_user(
            username="regularuser",
            email="user@example.com",
            password="password123",
            role="Applicant"
        )

    def test_create_notification_for_admin(self):
        """Test that a notification is created for an admin user with the given parameters."""
        title = "Test Title"
        message = "Test message content."
        notification_type = "job"
        priority = "high"
        related_object_id = 42
        related_object_type = "job"
        action_url = "/test/action/"

        initial_count = Notification.objects.count()

        create_admin_notification(
            user=self.admin_user,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            related_object_id=related_object_id,
            related_object_type=related_object_type,
            action_url=action_url
        )

        # Check that one new notification was created.
        self.assertEqual(Notification.objects.count(), initial_count + 1)
        notif = Notification.objects.latest('id')
        self.assertEqual(notif.recipient, self.admin_user)
        self.assertEqual(notif.title, title)
        self.assertEqual(notif.message, message)
        self.assertEqual(notif.notification_type, notification_type)
        self.assertEqual(notif.priority, priority)
        self.assertEqual(notif.related_object_id, related_object_id)
        self.assertEqual(notif.related_object_type, related_object_type)
        self.assertEqual(notif.action_url, action_url)
        self.assertFalse(notif.is_read)

    def test_no_notification_for_non_admin(self):
        """Test that no notification is created if the user is not an admin."""
        initial_count = Notification.objects.count()

        create_admin_notification(
            user=self.non_admin_user,
            title="Should not create",
            message="No notification",
            notification_type="general",
            priority="medium"
        )

        # Count should remain the same.
        self.assertEqual(Notification.objects.count(), initial_count)
