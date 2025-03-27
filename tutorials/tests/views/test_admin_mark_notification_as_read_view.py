from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.admin_models import Notification

User = get_user_model()

class MarkNotificationAsReadTests(TestCase):
    def setUp(self):
        self.client = Client()

        # Create an admin user
        self.admin_user = User.objects.create_user(
            username='admin', email='admin@example.com',
            password='adminpass', role='Admin', is_staff=True
        )

        # Create a non-admin user
        self.other_user = User.objects.create_user(
            username='user', email='user@example.com',
            password='userpass', role='Applicant'
        )

        # Create a notification for admin
        self.notification = Notification.objects.create(
            recipient=self.admin_user,
            message="Test notification"
        )

        self.url = reverse('admin_mark_notification_as_read', args=[self.notification.id])


    def test_mark_valid_notification_as_read(self):
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'success'})

        # Refresh from DB and check
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_notification_not_found(self):
        self.client.login(username='admin', password='adminpass')
        url = reverse('admin_mark_notification_as_read', args=[999])  # non-existent
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertIn("Notification not found", response.json()['message'])

    def test_notification_does_not_belong_to_user(self):
        self.client.login(username='user', password='userpass')
        url = reverse('admin_mark_notification_as_read', args=[self.notification.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("log_in"), response.url)

    def test_notification_wrong_recipient(self):
        self.notification.recipient = self.other_user
        self.notification.save()
        self.client.login(username='admin', password='adminpass')
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertIn("Permission denied", response.json()['message'])

    def test_unauthenticated_user(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)  # Redirect to login

