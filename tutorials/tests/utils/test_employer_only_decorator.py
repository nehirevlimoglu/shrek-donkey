# tutorials/tests/utils/test_employer_only_decorator.py

from django.test import TestCase, RequestFactory
from django.http import Http404, HttpResponse
from django.contrib.auth import get_user_model

# ✅ Import your real decorator
from tutorials.decorators import employer_only

User = get_user_model()

@employer_only
def protected_employer_view(request):
    return HttpResponse("Hello, Employer!")

class EmployerOnlyDecoratorTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

        # Create an employer user with unique email
        self.employer_user = User.objects.create_user(
            username="employeruser",
            password="testpass",
            email="employer@example.org",
            role="Employer"
        )

        # Create a non-employer user
        self.regular_user = User.objects.create_user(
            username="regularuser",
            password="testpass",
            email="regular@example.org",
            role="Admin"
        )

    def test_employer_only_allows_employer_user(self):
        """
        If user.role == 'Employer', the decorator should allow access,
        returning 200 and the view's content.
        """
        request = self.factory.get("/some-employer-url/")
        request.user = self.employer_user
        response = protected_employer_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Hello, Employer!")

    def test_employer_only_denies_non_employer_user(self):
        """
        If user.role != 'Employer', the decorator should raise Http404.
        """
        request = self.factory.get("/some-employer-url/")
        request.user = self.regular_user
        with self.assertRaises(Http404):
            protected_employer_view(request)
