from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

# Import your Application model from the appropriate module.
from tutorials.models.employer_models import Job, Employer
from tutorials.models.applicants_models import Applicant, Application # Assuming your Applicant model is here

User = get_user_model()

class ReviewApplicationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an applicant user.
        self.applicant_user = User.objects.create_user(
            username="applicantuser",
            email="applicant@example.com",
            password="password123",
            role="Applicant"
        )
        self.client.force_login(self.applicant_user)
        
        # Create an Applicant profile for this user.
        self.applicant = Applicant.objects.create(
            user=self.applicant_user,
            # Add other required fields if needed.
        )
        
        # Create an employer (needed for a Job).
        self.employer_user = User.objects.create_user(
            username="employeruser",
            email="employer@example.com",
            password="password123",
            role="Employer"
        )
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username="employeruser",
            email="employer@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )
        
        # Create a Job instance.
        from django.utils import timezone
        self.job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="Job description for testing",
            application_deadline=timezone.now().date() + timezone.timedelta(days=10)
        )
        
        # Create a dummy resume file.
        dummy_resume = SimpleUploadedFile(
            "resume.pdf",
            b"Dummy resume content",
            content_type="application/pdf"
        )
        
        # Create an Application instance.
        self.application = Application.objects.create(
            applicant=self.applicant,
            job=self.job,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="1234567890",
            address="123 Test St",
            education=[],            # using default empty list
            work_experience=[],      # using default empty list
            current_job_title="Developer",
            current_employer="Test Employer",
            linkedin_profile="",
            portfolio_website="",
            how_did_you_hear="other",
            sponsorship_needed="no",
            confirm_information=True,
            status="under_review",
            resume=dummy_resume
        )
        
        # Build the URL using the application_id.
        self.url = reverse("review_application", kwargs={"application_id": self.application.id})

    def test_review_application_view_success(self):
        """Test that a valid application ID returns the review page with the correct context."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "application_review.html")
        self.assertIn("application", response.context)
        self.assertEqual(response.context["application"].id, self.application.id)

    def test_review_application_view_not_found(self):
        """Test that an invalid application ID returns a 404 error."""
        invalid_url = reverse("review_application", kwargs={"application_id": 99999})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)
