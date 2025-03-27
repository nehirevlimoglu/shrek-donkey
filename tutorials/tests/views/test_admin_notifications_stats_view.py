from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from tutorials.models.admin_models import Notification

User = get_user_model()

class AdminNotificationStatsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="adminpass",
            role="Admin",
            is_staff=True,
        )
        self.client.login(username="adminuser", password="adminpass")
        self.url = reverse("admin_notifications_stats")

        # Create test notifications
        Notification.objects.create(recipient=self.admin_user, notification_type='general', priority='high', is_read=False)
        Notification.objects.create(recipient=self.admin_user, notification_type='job', priority='medium', is_read=True)
        Notification.objects.create(recipient=self.admin_user, notification_type='application', priority='low', is_read=False)
        Notification.objects.create(recipient=self.admin_user, notification_type='user', priority='low', is_read=True)
        Notification.objects.create(recipient=self.admin_user, notification_type='system', priority='medium', is_read=False)

    def test_admin_gets_correct_notification_stats(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data['total_count'], 5)
        self.assertEqual(data['unread_count'], 3)
        self.assertEqual(data['type_counts']['general'], 1)
        self.assertEqual(data['type_counts']['job'], 1)
        self.assertEqual(data['type_counts']['application'], 1)
        self.assertEqual(data['type_counts']['user'], 1)
        self.assertEqual(data['type_counts']['system'], 1)
        self.assertEqual(data['priority_counts']['high'], 1)
        self.assertEqual(data['priority_counts']['medium'], 2)
        self.assertEqual(data['priority_counts']['low'], 2)
        self.assertIn('feedback_count', data)

    def test_admin_with_no_notifications(self):
        Notification.objects.all().delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(data['total_count'], 0)
        self.assertEqual(data['unread_count'], 0)
        self.assertTrue(all(v == 0 for v in data['type_counts'].values()))
        self.assertTrue(all(v == 0 for v in data['priority_counts'].values()))
        self.assertEqual(data['feedback_count'], 0)

    def test_redirect_if_not_logged_in(self):
        self.client.logout()
        response = self.client.get(self.url)
        login_url = reverse("log_in")
        expected = f"{login_url}?next={self.url}"
        self.assertRedirects(response, expected)
