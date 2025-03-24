import json
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.contrib.messages import get_messages
from unittest.mock import patch

# Import models and forms.
from tutorials.models.employer_models import Employer, Job, Candidate, EmployerNotification
from tutorials.models.applicants_models import Applicant, ApplicantNotification, Application
from tutorials.forms.applicants_forms import ApplicationForm
from tutorials.utils import extract_skills_nlp  # Function we want to patch

User = get_user_model()

class ApplyForJobViewTests(TestCase):
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
        self.applicant_obj = Applicant.objects.create(user=self.applicant_user)
        
        # Create an employer and job.
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
        
        # Create a Candidate instance.
        from tutorials.models.employer_models import Candidate
        self.candidate = Candidate.objects.create(
            user=self.applicant_user,
            job=self.job,
            application_status="under_review",
            application_date=timezone.now(),
            first_name="John",
            last_name="Doe"
        )
        
        # Ensure no duplicate application exists.
        Application.objects.filter(applicant=self.applicant_obj, job=self.job).delete()
        
        self.url = reverse("apply_for_job", kwargs={"job_id": self.job.id})

    def get_valid_post_data(self):
        """Return a dictionary with valid POST data for the application form."""
        return {
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
            "confirm_information": "True",  # Adjust as needed (e.g. "True" or "on")
            "skills": "Python, Django",
            # Education list fields.
            "school[]": ["School A"],
            "degree[]": ["Bachelor"],
            "discipline[]": ["Computer Science"],
            "start_date[]": ["2010-01-01"],
            "end_date[]": ["2014-01-01"],
            # Work experience list fields.
            "work_job_title[]": ["Software Developer"],
            "work_employer[]": ["Company X"],
            "work_start_date[]": ["2015-01-01"],
            "work_end_date[]": ["2017-01-01"],
            "job_description[]": ["Worked on several projects"],
        }

    @patch("tutorials.utils.extract_skills_nlp", return_value=["python", "django"])
    def test_post_valid_application(self, mock_extract):
        """Test that a valid POST request creates an Application with proper education and work_experience data, updates Candidate, and redirects."""
        valid_data = self.get_valid_post_data()
        response = self.client.post(self.url, valid_data)
        expected_redirect = f"/job/{self.job.id}/?applied=true"
        self.assertRedirects(response, expected_redirect)
        
        # Verify that an Application was created.
        application = Application.objects.filter(applicant=self.applicant_obj, job=self.job).first()
        self.assertIsNotNone(application)
        self.assertEqual(application.education, [{
            "school": "School A",
            "degree": "Bachelor",
            "discipline": "Computer Science",
            "start_date": "2010-01-01",
            "end_date": "2014-01-01"
        }])
        self.assertEqual(application.work_experience, [{
            "work_job_title": "Software Developer",
            "work_employer": "Company X",
            "work_start_date": "2015-01-01",
            "work_end_date": "2017-01-01",
            "job_description": "Worked on several projects"
        }])
        
        # Verify that the Candidate record was created/updated.
        candidate = Candidate.objects.get(user=self.applicant_user, job=self.job)
        self.assertEqual(candidate.skills, "python, django")
        self.assertEqual(candidate.application_status, "Pending")
        
        # Verify notifications.
        emp_notif = EmployerNotification.objects.filter(employer=self.job.employer).first()
        app_notif = ApplicantNotification.objects.filter(applicant=self.applicant_obj).first()
        self.assertIsNotNone(emp_notif)
        self.assertIsNotNone(app_notif)
        
        # Check success message.
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Your application has been submitted successfully!" in m.message for m in messages))

    def test_post_invalid_application(self):
        """Test that an invalid POST (e.g., missing required first_name) re-renders the form with errors."""
        invalid_data = self.get_valid_post_data()
        invalid_data["first_name"] = ""
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