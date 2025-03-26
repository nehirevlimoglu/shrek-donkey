from django.test import TestCase
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta, date

from django.contrib.auth import get_user_model
from tutorials.models.employer_models import Employer, WorkExperience, Candidate, Job

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
            user=self.user,
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

        self.job = Job.objects.create(
            employer=self.employer,
            title="Software Engineer",
            description="Test job",
            application_deadline=timezone.now().date() + timedelta(days=7)
        )

        self.candidate = Candidate.objects.create(
            user=self.user,
            job=self.job,
            first_name="John",
            last_name="Doe",
            application_status="Pending"
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

    def test_recent_activity_updates_on_save(self):
        """
        Test that 'recent_activity' auto-updates whenever the Employer record is saved.
        """
        old_activity = self.employer.recent_activity
        # Force a slight delay or just artificially shift the clock
        # so we can see a difference in the updated timestamp
        # We'll do a small time shift
        self.employer.company_name = "TechHub Updated"
        self.employer.save()
        self.employer.refresh_from_db()
        self.assertNotEqual(self.employer.recent_activity, old_activity)

    def test_invalid_industry_choice(self):
        """
        Setting 'industry' to a value not in the choices should fail validation
        when we call full_clean().
        """
        self.employer.industry = "SpaceTravel"  # Not in the industry choices
        with self.assertRaises(ValidationError):
            self.employer.full_clean()

    def test_invalid_account_status_choice(self):
        """
        Setting account_status to a value not in the choices should fail validation.
        """
        self.employer.account_status = "Frozen"  # Not in ('Active','Suspended','Pending')
        with self.assertRaises(ValidationError):
            self.employer.full_clean()

    def test_invalid_subscription_plan_choice(self):
        """
        Setting subscription_plan to a value not in the choices should fail validation.
        """
        self.employer.subscription_plan = "Ultra"
        with self.assertRaises(ValidationError):
            self.employer.full_clean()
    def test_experience_with_and_without_end_date(self):
        # 1 year of finished work experience
        WorkExperience.objects.create(
            candidate=self.candidate,
            job_title="Engineer A",
            employer="Company A",
            start_date=date.today() - timedelta(days=365),
            end_date=date.today() - timedelta(days=1)
        )
        # Ongoing work experience
        WorkExperience.objects.create(
            candidate=self.candidate,
            job_title="Engineer B",
            employer="Company B",
            start_date=date.today() - timedelta(days=30),
            end_date=None  # triggers default to date.today()
        )

        years = self.candidate.total_experience_years
        self.assertGreater(years, 1)
        self.assertAlmostEqual(years, (364 + 30) / 365.25, delta=0.1)

    def test_no_experience(self):
        self.assertEqual(self.candidate.total_experience_years, 0)

    def test_only_ongoing_experience(self):
        WorkExperience.objects.create(
            candidate=self.candidate,
            job_title="Intern",
            employer="Org",
            start_date=date.today() - timedelta(days=90),
            end_date=None
        )
        years = self.candidate.total_experience_years
        self.assertAlmostEqual(years, 90 / 365.25, delta=0.05)
