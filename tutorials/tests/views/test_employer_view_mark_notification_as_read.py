from django.test import TestCase, Client
from django.urls import reverse, path
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.test.utils import override_settings
from unittest.mock import patch

from tutorials.models.employer_models import Employer, EmployerNotification
from tutorials.views.employer_views import mark_notification_as_read  # Adjust path if needed

User = get_user_model()

urlpatterns = [
    path(
        'employer/notifications/mark_read/<int:notification_id>/',
        mark_notification_as_read,
        name='mark_employer_notification_as_read'
    ),
    path('log_in/', lambda request: JsonResponse({'login': True}), name='log_in'),
]

@override_settings(ROOT_URLCONF=__name__)
class MarkEmployerNotificationAsReadTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.employer_user = User.objects.create_user(
            username="employer",
            email="employer@example.com",
            password="employerpass",
            role="Employer",
            is_staff=True,
        )

        self.employer = Employer.objects.create(
            user=self.employer_user,
            username="employer",
            email="employer@example.com",
            company_name="TestCorp",
            company_location="NYC",
            industry="Tech",
        )

        self.notification = EmployerNotification.objects.create(
            employer=self.employer,
            title="Test",
            message="Test notification",
            is_read=False,
            created_at=timezone.now(),
        )

        self.url = reverse("mark_employer_notification_as_read", args=[self.notification.id])

    def test_employer_can_mark_notification_as_read(self):
        self.client.login(username="employer", password="employerpass")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("success"))
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_get_request_returns_405(self):
        self.client.login(username="employer", password="employerpass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
        self.assertFalse(response.json().get("success"))

    def test_unauthenticated_user_redirected(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("log_in")))

    def test_user_not_employer(self):
        other_user = User.objects.create_user(
            username="applicant",
            email="applicant@example.com",
            password="pass",
            role="Applicant",
        )
        self.client.login(username="applicant", password="pass")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertIn("User is not an employer", response.json()["error"])

    def test_employer_object_missing(self):
        self.employer.delete()
        self.client.login(username="employer", password="employerpass")
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertIn("Employer not found", response.json()["error"])

    def test_notification_not_found(self):
        self.client.login(username="employer", password="employerpass")
        invalid_url = reverse("mark_employer_notification_as_read", args=[9999])
        response = self.client.post(invalid_url)
        self.assertEqual(response.status_code, 404)
        self.assertIn("Notification not found", response.json()["error"])

    def test_internal_server_error_simulation(self):
        self.client.login(username="employer", password="employerpass")
        with patch("tutorials.views.employer_views.Employer.objects.get", side_effect=Exception("Unexpected error")):
            response = self.client.post(self.url)
            self.assertEqual(response.status_code, 500)
            self.assertIn("error", response.json())
