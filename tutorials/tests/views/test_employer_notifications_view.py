from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from tutorials.models.employer_models import Employer
from tutorials.models.admin_models import Notification
User = get_user_model()

@override_settings(
    TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': False,
        'OPTIONS': {
            'loaders': [
                (
                    'django.template.loaders.locmem.Loader',
                    {
                        'employer_notifications.html': 'Dummy employer notifications template',
                        'error.html': 'Dummy error template: {{ message }}',
                        'log_in.html': 'Dummy login template'
                    }
                )
            ],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    }]
)
class EmployerNotificationsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an employer user.
        self.user = User.objects.create_user(
            username="employeruser",
            email="employer@example.com",
            password="password123",
            role="Employer"
        )
        self.client.force_login(self.user)
        # Create an Employer instance that matches request.user.username.
        self.employer = Employer.objects.create(
            user=self.user,
            username="employeruser",  # must match request.user.username
            email="employer@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )
        # Create some notifications for this employer with a dummy created_at.
        self.notification1 = Notification.objects.create(
            recipient=self.user,
            title="Notification 1",
            message="First notification",
            is_read=False,
            created_at=timezone.now()
        )
        self.notification2 = Notification.objects.create(
            recipient=self.user,
            title="Notification 2",
            message="Second notification",
            is_read=False,
            created_at=timezone.now()
        )
        # Create one notification for another user so it won't be returned.
        self.other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="password123",
            role="Employer"
        )
        Notification.objects.create(
            recipient=self.other_user,
            title="Other Notification",
            message="Not for employeruser",
            is_read=False,
            created_at=timezone.now()
        )
        self.url = reverse("employer_notifications")

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)

    def test_employer_notifications_view(self):
        """Test that a GET request returns the employer notifications page with notifications marked as read."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "employer_notifications.html")
        notifications = response.context["notifications"]
        # Check that only notifications for self.user are returned and that they are marked as read.
        for notif in notifications:
            self.assertEqual(notif.recipient, self.user)
            self.assertTrue(notif.is_read)
        # Check that notifications are ordered descending by created_at.
        created_dates = [notif.created_at for notif in notifications]
        self.assertEqual(created_dates, sorted(created_dates, reverse=True))

    def test_employer_notifications_employer_not_found(self):
        """Test that if the logged-in user does not have an Employer profile, a JSON error is returned with status 403."""
        # Create a user with role Employer but do not create an Employer profile.
        user_no_employer = User.objects.create_user(
            username="nouseremployer",
            email="nouseremployer@example.com",
            password="password123",
            role="Employer"
        )
        self.client.force_login(user_no_employer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        data = response.json()
        self.assertIn("error", data)
        self.assertEqual(data["error"], "Employer not found")