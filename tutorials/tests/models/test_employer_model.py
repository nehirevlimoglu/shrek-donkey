from django.contrib.auth import get_user_model
from django.test import TestCase
from tutorials.models.employer_models import Employer
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError

User = get_user_model()

class EmployerModelTest(TestCase):
    def setUp(self):
        """Create a sample employer instance linked to a user for testing."""
        self.user = User.objects.create_user(
            username="tech_hub_user",
            email="user@techhub.com",
            password="testpassword123"
        )

        self.employer = Employer.objects.create(
            user=self.user,  # ✅ Link the user here
            username="tech_hub",
            email="contact@techhub.com",
            company_name="TechHub",
            company_website="https://techhub.com",
            company_location="San Francisco",
            industry="Tech",
            company_size=50,
            total_jobs_posted=5,
            total_applicants=20,
            is_verified=True,
            account_status="Active",
            subscription_plan="Premium"
        )

    def test_create_employer(self):
        """Test if an employer instance is created successfully."""
        employer = Employer.objects.get(username="tech_hub")
        self.assertEqual(employer.email, "contact@techhub.com")
        self.assertEqual(employer.user.username, "tech_hub_user")
        self.assertEqual(employer.company_name, "TechHub")
        self.assertEqual(employer.company_size, 50)
        self.assertEqual(employer.account_status, "Active")
        self.assertEqual(employer.subscription_plan, "Premium")

    def test_unique_username_constraint(self):
        """Test that the username field must be unique."""
        user2 = User.objects.create_user(
            username="tech_hub_user2",
            email="user2@techhub.com",
            password="testpassword456"
        )
        with self.assertRaises(IntegrityError):
            Employer.objects.create(
                user=user2,
                username="tech_hub",  # Duplicate username
                email="newemail@company.com",
                company_name="New Company",
                company_location="Los Angeles",
                industry="Tech"
            )

    def test_unique_email_constraint(self):
        """Test that the email field must be unique."""
        user2 = User.objects.create_user(
            username="unique_username",
            email="uniqueuser@company.com",
            password="testpassword789"
        )
        with self.assertRaises(IntegrityError):
            Employer.objects.create(
                user=user2,
                username="new_username",
                email="contact@techhub.com",  # Duplicate email
                company_name="AnotherTech",
                company_location="Seattle",
                industry="Tech"
            )

    def test_default_values(self):
        """Test that default values are correctly set."""
        user3 = User.objects.create_user(
            username="new_employer_user",
            email="newuser@company.com",
            password="password1234"
        )
        employer = Employer.objects.create(
            user=user3,
            username="new_employer",
            email="new@company.com",
            company_name="New Co",
            company_location="New York",
            industry="Retail"
        )
        self.assertEqual(employer.total_jobs_posted, 0)
        self.assertEqual(employer.total_applicants, 0)
        self.assertEqual(employer.account_status, "Pending")
        self.assertEqual(employer.subscription_plan, "Free")

    def test_str_representation(self):
        """Test the string representation of Employer."""
        self.assertEqual(str(self.employer), "TechHub (tech_hub)")

    def test_company_size_cannot_be_negative(self):
        """Test that company size cannot be negative."""
        user4 = User.objects.create_user(
            username="negative_size_user",
            email="negativeuser@company.com",
            password="negativepass"
        )
        employer = Employer(
            user=user4,
            username="negative_size",
            email="negative@company.com",
            company_name="Negative Inc.",
            company_size=-10,  # Invalid size
            company_location="Chicago",
            industry="Tech"
        )
        with self.assertRaises(ValidationError):
            employer.full_clean()  # Explicitly run validation to trigger error

    def test_company_logo_blank_and_null(self):
        """Test that company_logo can be blank or null."""
        user5 = User.objects.create_user(
            username="logo_test_user",
            email="logo@test.com",
            password="logopass"
        )
        employer = Employer.objects.create(
            user=user5,
            username="logo_test",
            email="logo@test.com",
            company_name="LogoTest",
            company_location="Boston",
            industry="Tech"
        )
        self.assertFalse(employer.company_logo)

