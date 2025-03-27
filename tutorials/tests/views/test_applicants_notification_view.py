from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone

from tutorials.models.applicants_models import Applicant, ApplicantNotification
from tutorials.models.employer_models import Employer

User = get_user_model()

class ApplicantsNotificationsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create an applicant user and an Applicant instance.
        self.applicant_user = User.objects.create_user(
            username="applicantuser",
            password="testpass",
            role="Applicant",
            email="applicant@example.com"
        )
        self.applicant = Applicant.objects.create(
            user=self.applicant_user,
            degree="Bachelor"
        )
        
        # Create an employer user (non‑applicant) for negative tests.
        self.employer_user = User.objects.create_user(
            username="employeruser",
            password="testpass",
            role="Employer",
            email="employer@example.com"
        )
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username="employeruser",
            email="employer@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )
        
        # IMPORTANT: Use the URL name exactly as defined in urls.py.
        self.url = reverse("applicants-notifications")

    def test_redirect_if_not_logged_in(self):
        """Non-logged-in users should be redirected to the login page."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("log_in"), response.url)

    def test_forbidden_if_not_applicant(self):
        """
        If the logged-in user is not an applicant, 
        the view should return a 403 Forbidden.
        """
        self.client.login(username="employeruser", password="testpass")
        response = self.client.get(self.url)
        # Adjust this if your @applicant_only decorator behaves differently.
        self.assertEqual(response.status_code, 403)

    def test_no_notifications_for_applicant(self):
        """
        If the applicant has no notifications, the view should render the page
        with an empty notifications list.
        """
        self.client.login(username="applicantuser", password="testpass")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicants_notifications.html")
        self.assertIn("notifications", response.context)
        notifications = response.context["notifications"]
        self.assertEqual(notifications.count(), 0)

    def test_notifications_exist(self):
        """
        If the applicant has notifications, they should be returned in descending order by timestamp.
        """
        self.client.login(username="applicantuser", password="testpass")
        # Create two notifications with different timestamps.
        notif1 = ApplicantNotification.objects.create(
            applicant=self.applicant,
            title="Notification 1",
            message="First notification",
            timestamp=timezone.now() - timezone.timedelta(days=1)
        )
        notif2 = ApplicantNotification.objects.create(
            applicant=self.applicant,
            title="Notification 2",
            message="Second notification",
            timestamp=timezone.now()
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicants_notifications.html")
        notifications = response.context["notifications"]
        self.assertEqual(notifications.count(), 2)
        # Since notifications are ordered by '-timestamp', notif2 (newer) should come first.
        self.assertEqual(notifications[0], notif2)
        self.assertEqual(notifications[1], notif1)
