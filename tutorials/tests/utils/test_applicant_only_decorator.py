from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.urls import reverse

# ✅ Import the real decorator from decorators.py
from tutorials.decorators import applicant_only

User = get_user_model()

@applicant_only
def protected_applicant_view(request):
    return HttpResponse("Hello, Applicant!")

class ApplicantOnlyDecoratorTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # Create a user with role='Applicant'
        self.applicant_user = User.objects.create_user(
            username="applicantuser",
            password="testpass",
            email="applicant@example.org",
            role="Applicant"
        )

        # Create a user with role='job_seeker'
        self.job_seeker_user = User.objects.create_user(
            username="jobseeker",
            password="testpass",
            email="jobseeker@example.org",
            role="job_seeker"
        )

        # Create a user with a different role
        self.regular_user = User.objects.create_user(
            username="regularuser",
            password="testpass",
            email="regular@example.org",
            role="Admin"
        )

    def test_redirect_if_not_logged_in(self):
        """
        If user is not authenticated, we should redirect to login page (302).
        This covers lines 34-35 in the decorator.
        """
        request = self.factory.get("/applicant-only-url/")
        request.user = AnonymousUser()  # Not authenticated
        response = protected_applicant_view(request)

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('log_in'), response.url)
        self.assertIn("next=/applicant-only-url/", response.url)

    def test_applicant_role_allowed(self):
        """
        A user with role='Applicant' => line 42 is executed, returning 200.
        """
        request = self.factory.get("/applicant-only-url/")
        request.user = self.applicant_user
        response = protected_applicant_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Hello, Applicant!")

    def test_job_seeker_role_allowed(self):
        """
        A user with role='job_seeker' => also line 42 is executed, returning 200.
        """
        request = self.factory.get("/applicant-only-url/")
        request.user = self.job_seeker_user
        response = protected_applicant_view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Hello, Applicant!")

    def test_other_roles_raise_permission_denied(self):
        """
        If user.role is not 'Applicant' or 'job_seeker' => lines 38-39 cause PermissionDenied.
        """
        request = self.factory.get("/applicant-only-url/")
        request.user = self.regular_user
        with self.assertRaises(PermissionDenied):
            protected_applicant_view(request)
