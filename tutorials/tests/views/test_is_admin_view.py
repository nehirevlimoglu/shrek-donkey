from django.test import TestCase
from django.contrib.auth import get_user_model

# Import the function to test; adjust the import path as needed.
from tutorials.views.admin_views import is_admin

User = get_user_model()

class IsAdminTests(TestCase):

    def test_returns_true_for_user_with_admin_role(self):
        user = User(username="admin", role="Admin")
        self.assertTrue(is_admin(user))

    def test_returns_false_for_user_with_non_admin_role(self):
        user = User(username="applicant", role="Applicant")
        self.assertFalse(is_admin(user))

    def test_returns_false_if_user_has_no_role_attribute(self):
        class NoRoleUser:
            pass
        anon_user = NoRoleUser()
        self.assertFalse(is_admin(anon_user))

    def test_returns_false_for_none(self):
        self.assertFalse(is_admin(None))
