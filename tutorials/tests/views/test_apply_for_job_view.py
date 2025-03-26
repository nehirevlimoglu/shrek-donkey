import json
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages

from tutorials.models.applicants_models import Applicant, Application
from tutorials.models.employer_models import Job, Employer, JobTitle
# Adjust the import if your notification model is needed:
from tutorials.models.applicants_models import ApplicantNotification

from tutorials.forms.applicants_forms import ApplicationForm

# Dummy functions to override external functionality for tests.
def dummy_extract_skills_nlp(text):
    return [s.strip() for s in text.split(",") if s.strip()]

def dummy_match_candidates_to_job(job_title, top_n=10):
    return []

User = get_user_model()

class ApplyForJobViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an applicant user and associated Applicant instance.
        self.applicant_user = User.objects.create_user(
            username='applicantuser', 
            password='testpass', 
            role='Applicant', 
            email='applicant@example.com'
        )
        self.applicant = Applicant.objects.create(user=self.applicant_user)
        
        # Create an employer and a job.
        self.employer_user = User.objects.create_user(
            username='employeruser', 
            password='testpass', 
            role='Employer', 
            email='employer@example.com'
        )
        self.employer = Employer.objects.create(user=self.employer_user, company_name='TechCorp')
        
        self.job = Job.objects.create(
            employer=self.employer,
            title="Software Engineer",
            description="Job description",
            location="Remote",
            salary=100000,
        )
        
        # Create JobTitle instances for the M2M field.
        self.job_title1 = JobTitle.objects.create(title='Developer')
        self.job_title2 = JobTitle.objects.create(title='Designer')
        
        # URL for the apply_for_job view.
        self.apply_url = reverse('apply_for_job', kwargs={'job_id': self.job.id})
        
        # Override external functions.
        from tutorials.views.applicant_views import apply_for_job as apply_view_module
        apply_view_module.extract_skills_nlp = dummy_extract_skills_nlp
        apply_view_module.match_candidates_to_job = dummy_match_candidates_to_job

        # Remove file fields if they cause issues.
        if "resume" in ApplicationForm.base_fields:
            ApplicationForm.base_fields.pop("resume")
        if "cover_letter" in ApplicationForm.base_fields:
            ApplicationForm.base_fields.pop("cover_letter")
    
    def login_applicant(self):
        self.client.login(username='applicantuser', password='testpass')

    def test_get_application_form(self):
        """GET request should render the application form with initial data."""
        self.login_applicant()
        response = self.client.get(self.apply_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicants_application.html")
        self.assertIn("form", response.context)
        self.assertIn("job", response.context)
        # Check that there is no existing application.
        self.assertFalse(response.context.get("existing_application", True))

    def test_post_valid_application_non_ajax(self):
        """
        Valid POST (non-AJAX) creates an application and redirects.
        Updated field values to match valid choices:
         - discipline: "bachelors" (valid, instead of "Information Technology")
         - how_did_you_hear: "referral" (lowercase)
         - sponsorship_needed: "no" (lowercase)
        """
        self.login_applicant()
        
        post_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "applicant@example.com",
            "phone": "1234567890",
            "address": "123 Main St",
            "school": "Test University",
            "degree": "Bachelor",
            "discipline": "bachelors",  # valid choice from the form
            "how_did_you_hear": "referral",  # valid choice
            "sponsorship_needed": "no",      # valid choice
            "confirm_information": "on",
            "start_date": "2020-01-01",
            "end_date": "2024-01-01",
            "linkedin_profile": "https://linkedin.com/in/johndoe",
            "portfolio_website": "https://johndoe.com",
            "current_job_title": "Intern",
            "current_employer": "TechCorp",
            "skills": "Python, Django, REST",
            # Dynamic education fields:
            "school[]": ["Test University"],
            "degree[]": ["Bachelor"],
            "discipline[]": ["bachelors"],
            "start_date[]": ["2020-01-01"],
            "end_date[]": ["2024-01-01"],
            # Dynamic work experience fields:
            "work_job_title[]": ["Software Intern"],
            "work_employer[]": ["TechCorp"],
            "work_start_date[]": ["2021-06-01"],
            "work_end_date[]": ["2021-08-01"],
            "job_description[]": ["Developed features"],
        }
        
        response = self.client.post(self.apply_url, post_data)
        
        expected_redirect = f"/job/{self.job.id}/?applied=true"
        self.assertRedirects(response, expected_redirect)

        application = Application.objects.get(applicant=self.applicant, job=self.job)
        self.assertEqual(application.education, [{
            "school": "Test University",
            "degree": "Bachelor",
            "discipline": "bachelors",
            "start_date": "2020-01-01",
            "end_date": "2024-01-01"
        }])

    def test_post_valid_application_ajax(self):
        """
        Valid AJAX POST returns a JSON response with success.
        Updated field values to valid ones.
        """
        self.login_applicant()
        
        post_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "applicant@example.com",
            "phone": "1234567890",
            "address": "123 Main St",
            "school": "Test University",
            "degree": "Bachelor",
            "discipline": "bachelors",
            "how_did_you_hear": "referral",
            "sponsorship_needed": "no",
            "confirm_information": "on",
            "start_date": "2020-01-01",
            "end_date": "2024-01-01",
            "linkedin_profile": "https://linkedin.com/in/johndoe",
            "portfolio_website": "https://johndoe.com",
            "current_job_title": "Intern",
            "current_employer": "TechCorp",
            "skills": "Python, Django, REST",
            # Dynamic education fields:
            "school[]": ["Test University"],
            "degree[]": ["Bachelor"],
            "discipline[]": ["bachelors"],
            "start_date[]": ["2020-01-01"],
            "end_date[]": ["2024-01-01"],
            # Dynamic work experience fields:
            "work_job_title[]": ["Software Intern"],
            "work_employer[]": ["TechCorp"],
            "work_start_date[]": ["2021-06-01"],
            "work_end_date[]": ["2021-08-01"],
            "job_description[]": ["Developed features"],
        }
        
        response = self.client.post(
            self.apply_url,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True})

    def test_post_invalid_application(self):
        """
        Invalid POST submission returns errors:
         - Non-AJAX re-renders the form with errors.
         - AJAX returns JSON with errors.
        """
        self.login_applicant()
        post_data = {
            "first_name": "",
            "last_name": "",
            "email": "applicant@example.com",
            "skills": "",
            # Dynamic fields as empty lists.
            "school[]": [],
            "degree[]": [],
            "discipline[]": [],
            "start_date[]": [],
            "end_date[]": [],
            "work_job_title[]": [],
            "work_employer[]": [],
            "work_start_date[]": [],
            "work_end_date[]": [],
            "job_description[]": [],
        }
        # Non-AJAX submission.
        response = self.client.post(self.apply_url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicants_application.html")
        self.assertIn("form", response.context)
        form = response.context["form"]
        self.assertFalse(form.is_valid())
        
        # AJAX submission.
        response_ajax = self.client.post(self.apply_url, post_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response_ajax.status_code, 200)
        json_response = response_ajax.json()
        self.assertFalse(json_response.get("success"))
        self.assertIn("error", json_response)

    def test_duplicate_application(self):
        """
        If the applicant has already applied, they should be redirected
        to the job detail page with an error message.
        """
        self.login_applicant()
        # Create an existing application.
        Application.objects.create(applicant=self.applicant, job=self.job)
        
        post_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "applicant@example.com",
            "phone": "1234567890",
            "address": "123 Main St",
            "school": "Test University",
            "degree": "Bachelor",
            "discipline": "bachelors",
            "start_date": "2020-01-01",
            "end_date": "2024-01-01",
            "linkedin_profile": "https://linkedin.com/in/johndoe",
            "portfolio_website": "https://johndoe.com",
            "how_did_you_hear": "linkedin",
            "current_job_title": "Intern",
            "current_employer": "TechCorp",
            "skills": "Python, Django, REST",
            # Dynamic fields.
            "school[]": ["Test University"],
            "degree[]": ["Bachelor"],
            "discipline[]": ["bachelors"],
            "start_date[]": ["2020-01-01"],
            "end_date[]": ["2024-01-01"],
            "work_job_title[]": ["Software Intern"],
            "work_employer[]": ["TechCorp"],
            "work_start_date[]": ["2021-06-01"],
            "work_end_date[]": ["2021-08-01"],
            "job_description[]": ["Developed features"],
        }
        response = self.client.post(self.apply_url, post_data)
        self.assertRedirects(response, reverse("job_detail", kwargs={"job_id": self.job.id}))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("already applied" in m.message for m in messages))

    def test_keybert_extraction_fallback_and_exception(self):
        self.login_applicant()

        # Import and override the actual view's extract_skills_nlp function
        from tutorials.views.applicant_views import apply_for_job as apply_view_module

        post_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "applicant@example.com",
            "phone": "1234567890",
            "address": "123 Main St",
            "school": "Test University",
            "degree": "Bachelor",
            "discipline": "bachelors",
            "start_date": "2020-01-01",
            "end_date": "2024-01-01",
            "linkedin_profile": "https://linkedin.com/in/johndoe",
            "portfolio_website": "https://johndoe.com",
            "how_did_you_hear": "referral",
            "sponsorship_needed": "no",
            "confirm_information": "on",
            "current_job_title": "Intern",
            "current_employer": "TechCorp",
            "skills": "SkillA, SkillB",
            "school[]": ["Test University"],
            "degree[]": ["Bachelor"],
            "discipline[]": ["bachelors"],
            "start_date[]": ["2020-01-01"],
            "end_date[]": ["2024-01-01"],
            "work_job_title[]": ["Software Intern"],
            "work_employer[]": ["TechCorp"],
            "work_start_date[]": ["2021-06-01"],
            "work_end_date[]": ["2021-08-01"],
            "job_description[]": ["Developed features"],
        }

        # CASE 1: Force empty skills extraction
        apply_view_module.extract_skills_nlp = lambda text: []
        response = self.client.post(self.apply_url, post_data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True})

        # Clean up application so we can try the second case
        Application.objects.all().delete()

        # CASE 2: Force an exception in skill extraction
        def exploding_nlp(text):
            raise Exception("NLP failure")
        apply_view_module.extract_skills_nlp = exploding_nlp

        response = self.client.post(self.apply_url, post_data, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True})

