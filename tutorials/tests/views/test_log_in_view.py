# tutorials/tests/views/test_log_in_view.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.employer_models import Employer

User = get_user_model()

class LogInViewTests(TestCase):

    def setUp(self):
        self.client = Client()

        # Ensure unique emails to avoid IntegrityError
        self.admin_user = User.objects.create_user(
            username="adminuser", password="adminpass", role="Admin", email="admin@example.com"
        )

        self.employer_user = User.objects.create_user(
            username="employeruser", password="employerpass", role="Employer", email="employer@example.com"
        )

        self.applicant_user = User.objects.create_user(
            username="applicantuser", password="applicantpass", role="Applicant", email="applicant@example.com"
        )

    def test_admin_login_redirects_to_admin_home(self):
        response = self.client.post(reverse("log_in"), {"username": "adminuser", "password": "adminpass"})
        self.assertRedirects(response, reverse("admin_home_page"))

    def test_applicant_login_redirects_to_applicants_home(self):
        response = self.client.post(reverse("log_in"), {"username": "applicantuser", "password": "applicantpass"})
        self.assertRedirects(response, reverse("applicants-home-page"))

    def test_invalid_login_shows_error_message(self):
        response = self.client.post(reverse("log_in"), {"username": "wronguser", "password": "wrongpass"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Incorrect username or password")

    def test_missing_username_or_password(self):
        response = self.client.post(reverse("log_in"), {"username": "", "password": ""})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Incorrect username or password")

    def test_unknown_role_raises_404(self):
        unknown_role_user = User.objects.create_user(
            username="unknownrole", password="unknownpass", role="Unknown", email="unknown@example.com"
        )

        response = self.client.post(reverse("log_in"), {"username": "unknownrole", "password": "unknownpass"})
        self.assertEqual(response.status_code, 404)

    def test_csrf_cookie_set_on_get(self):
        response = self.client.get(reverse("log_in"))
        self.assertEqual(response.status_code, 200)
        self.assertIn('csrftoken', response.cookies)
        self.assertEqual(response.cookies['csrftoken']['samesite'], 'Lax')