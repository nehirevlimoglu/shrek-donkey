from django.test import TestCase
from django.contrib.auth import get_user_model

from tutorials.views.employer_views import is_employer

User = get_user_model()

class IsEmployerTests(TestCase):

    def test_returns_true_for_user_with_employer_role(self):
        user = User(username="employer", role="Employer")
        self.assertTrue(is_employer(user))

    def test_returns_false_for_user_with_non_employer_role(self):
        user = User(username="applicant", role="Applicant")
        self.assertFalse(is_employer(user))

    def test_returns_false_if_user_has_no_role_attribute(self):
        class NoRoleUser:
            pass
        anon_user = NoRoleUser()
        self.assertFalse(is_employer(anon_user))

    def test_returns_false_for_none(self):
        self.assertFalse(is_employer(None))