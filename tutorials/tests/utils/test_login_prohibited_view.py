# tutorials/tests/utils/test_login_prohibited_view.py

from django.test import TestCase, RequestFactory, override_settings
from django.http import HttpResponse
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

# Import your real decorator from helpers (or wherever you defined it)
from tutorials.helpers import login_prohibited

User = get_user_model()

@login_prohibited
def dummy_view(request):
    return HttpResponse("Public dummy content.")

@override_settings(
    REDIRECT_URL_WHEN_LOGGED_IN_ADMIN="admin_home_page",
    REDIRECT_URL_WHEN_LOGGED_IN_EMPLOYER="employer_home_page",
    REDIRECT_URL_WHEN_LOGGED_IN_APPLICANT="applicants-home-page",
    REDIRECT_URL_WHEN_LOGGED_IN="log_in",
)
class LoginProhibitedDecoratorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        self.admin_user = User.objects.create_user(
            username="admin_user",
            email="admin@example.org",  # unique
            password="testpass",
            role="Admin"
        )
        self.employer_user = User.objects.create_user(
            username="employer_user",
            email="employer@example.org",  # also unique
            password="testpass",
            role="Employer"
        )
        self.applicant_user = User.objects.create_user(
            username="applicant_user",
            email="applicant@example.org",  # also unique
            password="testpass",
            role="Applicant"
        )
        self.regular_user = User.objects.create_user(
            username="regular_user",
            email="regular@example.org",   # also unique
            password="testpass",
            role="SomethingElse"
        )


    def test_anonymous_user_access(self):
        """Unauthenticated user => no redirect, gets view content."""
        request = self.factory.get("/test-anonymous/")
        request.user = AnonymousUser()

        response = dummy_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Public dummy content.")

    def test_admin_redirect(self):
        """Authenticated Admin => redirect to /admin_home_page/."""
        request = self.factory.get("/test-admin/")
        request.user = self.admin_user

        response = dummy_view(request)
        self.assertEqual(response.status_code, 302)
        # Because 'admin_home_page' is a route name, Django reverses it => "/admin_home_page/"
        self.assertEqual(response.url, reverse("admin_home_page"))

    def test_employer_redirect(self):
        """Authenticated Employer => redirect to /employer_home_page/."""
        request = self.factory.get("/test-employer/")
        request.user = self.employer_user

        response = dummy_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("employer_home_page"))

    def test_applicant_redirect(self):
        """Authenticated Applicant => redirect to /applicants_home_page/."""
        request = self.factory.get("/test-applicant/")
        request.user = self.applicant_user

        response = dummy_view(request)
        self.assertEqual(response.status_code, 302)
        # 'applicants-home-page' is the name => /applicants_home_page/
        self.assertEqual(response.url, reverse("applicants-home-page"))

    def test_other_role_redirect(self):
        """Authenticated user with another role => redirect to /home_page/."""
        request = self.factory.get("/test-other/")
        request.user = self.regular_user

        response = dummy_view(request)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("log_in"))
