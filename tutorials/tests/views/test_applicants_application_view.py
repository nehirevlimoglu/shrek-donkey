from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.utils import timezone
from datetime import timedelta

# Import models and forms. Adjust import paths as needed.
from tutorials.models.employer_models import Job, Employer
from tutorials.models.applicants_models import Applicant, Application
from tutorials.forms.applicants_forms import ApplicationForm  # Assuming your form is here

User = get_user_model()

class ApplicantsApplicationViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()
        # Create an applicant user.
        self.applicant_user = User.objects.create_user(
            username="applicantuser",
            email="applicant@example.com",
            password="password123",
            role="Applicant"
        )
        self.client.force_login(self.applicant_user)
        
        # Create an Applicant profile for the user.
        self.applicant_obj = Applicant.objects.create(
            user=self.applicant_user,
            # Add any additional required fields.
        )
        
        # Create an employer and a job.
        self.employer_user = User.objects.create_user(
            username="employeruser",
            email="employer@example.com",
            password="password123",
            role="Employer"
        )
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username="employeruser",  # Must match if using request.user.username for lookup.
            email="employer@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )
        self.job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="Job description",
            application_deadline=self.today + timedelta(days=10)
        )
        
        # Create a Candidate instance for the applicant.
        from tutorials.models.employer_models import Candidate
        self.candidate = Candidate.objects.create(
            user=self.applicant_user,
            job=self.job,
            application_status="under_review",
            application_date=timezone.now(),
            first_name="John",
            last_name="Doe"
        )
        
        # Build the URL for the view using the job id.
        self.url = reverse("applicants_application", kwargs={"job_id": self.job.id})

    def test_get_applicants_application_view(self):
        """Test that a GET request renders the application form with the job in context."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicants_application.html")
        self.assertIn("form", response.context)
        self.assertIn("job", response.context)
        self.assertIsInstance(response.context["form"], ApplicationForm)

    def test_application_already_exists(self):
        """Test that if an application already exists, a warning is issued and the user is redirected."""
        # Create an Application for this applicant and job.
        Application.objects.create(
            applicant=self.applicant_obj,
            job=self.job,
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com",
            phone="1234567890",
            address="123 Main St",
            education=[],
            work_experience=[],
            current_job_title="Developer",
            current_employer="Some Company",
            linkedin_profile="",
            portfolio_website="",
            how_did_you_hear="other",
            sponsorship_needed="no",
            confirm_information=True,
            status="under_review"
        )
        response = self.client.get(self.url)
        # Expect a warning message and a redirect.
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("You have already applied for this job." in m.message for m in messages))
        expected_redirect = reverse("job_detail", kwargs={"pk": self.job.id})
        self.assertRedirects(response, expected_redirect)

    def test_post_valid_application(self):
        """Test that a valid POST creates an Application with proper JSON fields and redirects."""
        # Prepare valid form data.
        valid_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "1234567890",
            "address": "123 Main St",
            "current_job_title": "Developer",
            "current_employer": "Some Company",
            "linkedin_profile": "",
            "portfolio_website": "",
            "how_did_you_hear": "other",
            "sponsorship_needed": "no",
            # For checkboxes, the form might expect "True" or "on". Adjust accordingly.
            "confirm_information": "on",
            # List fields submitted as lists:
            "school[]": ["School A"],
            "degree[]": ["Bachelor"],
            "discipline[]": ["Computer Science"],
            "start_date[]": ["2010-01-01"],
            "end_date[]": ["2014-01-01"],
            "work_job_title[]": ["Software Developer"],
            "work_employer[]": ["Company X"],
            "work_start_date[]": ["2015-01-01"],
            "work_end_date[]": ["2017-01-01"],
            "job_description[]": ["Worked on several projects"],
        }
        response = self.client.post(self.url, valid_data)
        # Expect a redirect to job_detail.
        expected_redirect = reverse("job_detail", kwargs={"job_id": self.job.id})
        self.assertRedirects(response, expected_redirect)
        # Verify that an Application was created.
        application = Application.objects.filter(applicant=self.applicant_obj, job=self.job).first()
        self.assertIsNotNone(application)
        # Verify education JSON.
        self.assertEqual(application.education, [{
            "school": "School A",
            "degree": "Bachelor",
            "discipline": "Computer Science",
            "start_date": "2010-01-01",
            "end_date": "2014-01-01"
        }])
        # Verify work_experience JSON.
        self.assertEqual(application.work_experience, [{
            "work_job_title": "Software Developer",
            "work_employer": "Company X",
            "work_start_date": "2015-01-01",
            "work_end_date": "2017-01-01",
            "job_description": "Worked on several projects"
        }])
        # Check success message.
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Your application has been submitted successfully!" in m.message for m in messages))

    def test_post_invalid_application(self):
        """Test that an invalid POST re-renders the form with errors."""
        # For example, omit required first_name.
        invalid_data = {
            "first_name": "",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "1234567890",
            "address": "123 Main St",
            "current_job_title": "Developer",
            "current_employer": "Some Company",
            "linkedin_profile": "",
            "portfolio_website": "",
            "how_did_you_hear": "other",
            "sponsorship_needed": "no",
            "confirm_information": "True",
            "school[]": ["School A"],
            "degree[]": ["Bachelor"],
            "discipline[]": ["Computer Science"],
            "start_date[]": ["2010-01-01"],
            "end_date[]": ["2014-01-01"],
            "work_job_title[]": ["Software Developer"],
            "work_employer[]": ["Company X"],
            "work_start_date[]": ["2015-01-01"],
            "work_end_date[]": ["2017-01-01"],
            "job_description[]": ["Worked on several projects"],
        }
        response = self.client.post(self.url, invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicants_application.html")
        form = response.context.get("form")
        self.assertIsNotNone(form)
        self.assertTrue(form.errors)

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)