from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.employer_models import Employer

User = get_user_model()

class EmployerSettingsViewTests(TestCase):
    def setUp(self):
        self.client = Client()

        self.user = User.objects.create_user(
            username="@damla",
            password="Password123",
            role="Employer",
            email="damla@example.org",
        )

        self.employer = Employer.objects.create(
            user=self.user,
            username="@damla",
            email="damla@example.org",
            company_name="Damla Corp",
            company_location="London",
            industry="Tech",
        )

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(reverse("employer_settings"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("log_in"), response.url)

    def test_employer_settings_loads_correctly(self):
        self.client.login(username="@damla", password="Password123")
        response = self.client.get(reverse("employer_settings"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "employer_settings.html")
