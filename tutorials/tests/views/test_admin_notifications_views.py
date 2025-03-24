from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

# Import your Notification model. Adjust the import path as needed.
from tutorials.models.admin_models import Notification  
# If Notification is defined in another module, update the path accordingly.

User = get_user_model()

class AdminNotificationsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()
        # Create an admin user (role "Admin")
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin"
        )
        # Log in as the admin user.
        self.client.login(username="adminuser", password="password123")
        self.url = reverse("admin_notifications")
        
        # Create several Notification objects.
        # Assume Notification has fields: title, message, notification_type, priority, is_read, is_deleted.
        Notification.objects.create(
            recipient=self.admin_user,
            title="General 1",
            message="General message",
            notification_type="general",
            priority="high",
            is_read=False,
            is_deleted=False
        )
        Notification.objects.create(
            recipient=self.admin_user,
            title="Job 1",
            message="Job message",
            notification_type="job",
            priority="medium",
            is_read=True,
            is_deleted=False
        )
        Notification.objects.create(
            recipient=self.admin_user,
            title="Feedback 1",
            message="Feedback message",
            notification_type="feedback",
            priority="low",
            is_read=False,
            is_deleted=False
        )
        # Create additional notifications to test pagination.
        for i in range(15):
            Notification.objects.create(
                recipient=self.admin_user,  # ← this is the key!
                title=f"Test {i}",
                message="Test message",
                notification_type="application",
                priority="low",
                is_read=False,
                is_deleted=False
            )


    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)

    def test_filter_by_notification_type(self):
        """Test filtering notifications by type."""
        response = self.client.get(self.url, {"type": "job"})
        self.assertEqual(response.status_code, 200)
        for notif in response.context["notifications"]:
            self.assertEqual(notif.notification_type, "job")

    def test_filter_by_priority(self):
        """Test filtering notifications by priority."""
        response = self.client.get(self.url, {"priority": "high"})
        self.assertEqual(response.status_code, 200)
        for notif in response.context["notifications"]:
            self.assertEqual(notif.priority, "high")

    def test_filter_by_is_read(self):
        """Test filtering notifications by read status."""
        # Test for unread notifications.
        response_unread = self.client.get(self.url, {"is_read": "unread"})
        self.assertEqual(response_unread.status_code, 200)
        for notif in response_unread.context["notifications"]:
            self.assertFalse(notif.is_read)
        # Test for read notifications.
        response_read = self.client.get(self.url, {"is_read": "read"})
        self.assertEqual(response_read.status_code, 200)
        for notif in response_read.context["notifications"]:
            self.assertTrue(notif.is_read)

    def test_search_filter(self):
        """Test that the search filter returns notifications matching the query."""
        response = self.client.get(self.url, {"search": "Feedback"})
        self.assertEqual(response.status_code, 200)
        # At least one notification should contain "Feedback" in its title or message.
        found = any("feedback" in notif.title.lower() or "feedback" in notif.message.lower()
                    for notif in response.context["notifications"])
        self.assertTrue(found)

    def test_pagination(self):
        """Test that pagination returns at most 10 notifications per page."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # The paginator is set to 10 per page.
        notifications_page = response.context["notifications"]
        self.assertLessEqual(len(notifications_page.object_list), 10)

    def test_context_counts(self):
        """Test that context counts (total_count, unread_count, feedback_count, type_counts, priority_counts) are correct."""
        # Calculate expected counts.
        total_count = Notification.objects.filter(is_deleted=False).count()
        unread_count = Notification.objects.filter(is_deleted=False, is_read=False).count()
        feedback_count = Notification.objects.filter(is_deleted=False, notification_type="feedback").count()
        
        type_counts = {
            'general': Notification.objects.filter(is_deleted=False, notification_type="general").count(),
            'job': Notification.objects.filter(is_deleted=False, notification_type="job").count(),
            'application': Notification.objects.filter(is_deleted=False, notification_type="application").count(),
            'user': Notification.objects.filter(is_deleted=False, notification_type="user").count(),
            'system': Notification.objects.filter(is_deleted=False, notification_type="system").count(),
            'feedback': Notification.objects.filter(is_deleted=False, notification_type="feedback").count(),
        }
        
        priority_counts = {
            'high': Notification.objects.filter(is_deleted=False, priority="high").count(),
            'medium': Notification.objects.filter(is_deleted=False, priority="medium").count(),
            'low': Notification.objects.filter(is_deleted=False, priority="low").count(),
        }
        
        response = self.client.get(self.url)
        self.assertEqual(response.context["total_count"], total_count)
        self.assertEqual(response.context["unread_count"], unread_count)
        self.assertEqual(response.context["feedback_count"], feedback_count)
        self.assertEqual(response.context["type_counts"], type_counts)
        self.assertEqual(response.context["priority_counts"], priority_counts)
