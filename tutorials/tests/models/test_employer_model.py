from django.test import TestCase
from tutorials.models.employer_models import Employer
from django.db.utils import IntegrityError



class EmployerModelTest(TestCase):
    def setUp(self):
        """Create a sample employer instance for testing."""
        self.employer = Employer.objects.create(
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
        self.assertEqual(employer.company_name, "TechHub")
        self.assertEqual(employer.company_size, 50)
        self.assertEqual(employer.account_status, "Active")
        self.assertEqual(employer.subscription_plan, "Premium")

    def test_unique_username_constraint(self):
        """Test that the username field must be unique."""
        with self.assertRaises(IntegrityError):
            Employer.objects.create(
                username="tech_hub",  # Duplicate username
                email="newemail@company.com",
                company_name="New Company",
            )

    def test_unique_email_constraint(self):
        """Test that the email field must be unique."""
        with self.assertRaises(IntegrityError):
            Employer.objects.create(
                username="new_username",
                email="contact@techhub.com",  # Duplicate email
                company_name="AnotherTech"
            )

    def test_default_values(self):
        """Test that default values are correctly set."""
        employer = Employer.objects.create(
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
        with self.assertRaises(ValueError):
            employer = Employer.objects.create(
                username="negative_size",
                email="negative@company.com",
                company_name="Negative Inc.",
                company_size=-10  # Invalid
            )
            employer.full_clean()  # Ensures model validations are applied

    def test_company_logo_blank_and_null(self):
        """Test that company_logo can be blank or null."""
        employer = Employer.objects.create(
            username="logo_test",
            email="logo@test.com",
            company_name="LogoTest"
        )
        self.assertIsNone(employer.company_logo)  # Should be None by default
