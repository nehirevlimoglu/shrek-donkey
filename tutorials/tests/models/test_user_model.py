# tutorials/tests/models/test_user_model.py

import re
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self):
        # Create a simple user for baseline tests
        # Must pass the custom username regex ^@\w{3,}$
        self.user = User.objects.create_user(
            username='@abcde',
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            password='testpassword',
            role='Applicant'
        )

    def test_username_validation_success(self):
        """
        Test that a valid username (@abcde) meets the regex requirement.
        """
        # This user is valid because we created it in setUp
        self.user.full_clean()  # Should not raise ValidationError

    def test_username_validation_failure(self):
        """
        If username doesn't match ^@\\w{3,}$, it should fail validation.
        E.g. missing '@', or too short.
        """
        invalid_user = User(
            username='abc',  # Missing '@'
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            role='Employer'
        )
        with self.assertRaises(ValidationError):
            invalid_user.full_clean()

        another_user = User(
            username='@ab',  # Only 2 chars after '@'
            first_name='Tim',
            last_name='Short',
            email='tim@example.com',
            role='Admin'
        )
        with self.assertRaises(ValidationError):
            another_user.full_clean()

    def test_email_uniqueness(self):
        """
        Creating a second user with the same email should fail if
        email is unique=True.
        """
        with self.assertRaises(ValidationError):
            user2 = User(
                username='@unique2',
                first_name='Unique',
                last_name='Two',
                email='john@example.com',  # same as self.user
                role='Applicant'
            )
            user2.full_clean()  # triggers the uniqueness check

    def test_role_choices(self):
        """
        Role must be one of ['Employer','Applicant','Admin'].
        """
        self.user.role = 'NotAValidRole'
        with self.assertRaises(ValidationError):
            self.user.full_clean()

    def test_full_name_method(self):
        """
        full_name() should return 'John Doe' for our test user.
        """
        self.assertEqual(self.user.full_name(), 'John Doe')

    def test_gravatar_method(self):
        """
        gravatar(size=120) should return a URL with the user's email hash
        and 's=120'.
        """
        grav_url = self.user.gravatar(size=120)
        self.assertIn('gravatar.com/avatar/', grav_url)
        self.assertIn('size=120', grav_url)

        # You can also test the hashed email if needed:
        # e.g. import hashlib; check the MD5 of self.user.email.lower().strip()

    def test_mini_gravatar_method(self):
        """
        mini_gravatar() calls gravatar(size=60).
        """
        mini_url = self.user.mini_gravatar()
        self.assertIn('gravatar.com/avatar/', mini_url)
        self.assertIn('size=60', mini_url)
