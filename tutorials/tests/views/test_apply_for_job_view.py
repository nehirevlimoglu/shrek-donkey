from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.contrib.messages import get_messages

# Import your models and forms.
from tutorials.models.applicants_models import Applicant, Application, ApplicantNotification
from tutorials.models.employer_models import Job, Employer, JobTitle, WorkExperience, Candidate, EmployerNotification
from tutorials.forms.applicants_forms import ApplicationForm
# Import the view from the correct module.
from tutorials.views.applicant_views import apply_for_job

# Dummy functions for predictable behavior in tests.
def dummy_extract_skills_nlp(text):
    # Simply split the text by comma and strip whitespace.
    return [s.strip() for s in text.split(",") if s.strip()]

def dummy_match_candidates_to_job(job_title, top_n=10):
    # Return an empty list for simplicity.
    return []

User = get_user_model()

class ApplyForJobViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an applicant user and associated Applicant instance.
        self.applicant_user = User.objects.create_user(
            username='applicantuser', password='testpass', role='Applicant', email='applicant@example.com'
        )
        self.applicant = Applicant.objects.create(user=self.applicant_user)
        
        # Create an employer and a job.
        self.employer_user = User.objects.create_user(
            username='employeruser', password='testpass', role='Employer', email='employer@example.com'
        )
        self.employer = Employer.objects.create(user=self.employer_user, company_name='TechCorp')
        
        self.job = Job.objects.create(
            employer=self.employer,
            title="Software Engineer",
            description="Job description",
            location="Remote",
            salary=100000,
        )
        
        # Create JobTitle instances if needed.
        self.job_title1 = JobTitle.objects.create(title='Developer')
        self.job_title2 = JobTitle.objects.create(title='Designer')
        
        # URL for apply_for_job view.
        self.apply_url = reverse('apply_for_job', kwargs={'job_id': self.job.id})
        
        # Monkey-patch external functions by importing from the correct module.
        from tutorials.views.applicant_views import apply_for_job as apply_view_module
        apply_view_module.extract_skills_nlp = dummy_extract_skills_nlp
        apply_view_module.match_candidates_to_job = dummy_match_candidates_to_job

        # Optionally, if your ApplicationForm still defines file fields, you might
        # update its __init__ to ignore them or assume they're not required.
        # For our tests we assume resume and cover_letter are removed.
        # (Make sure your form and view can handle the absence of these fields.)

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
        """Valid POST (non-AJAX) creates an application, candidate, saves dynamic education/work data, and redirects."""
        self.login_applicant()
        
        # Build POST data without file fields.
        post_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "applicant@example.com",
            "phone": "1234567890",
            "address": "123 Main St",
            "school": "Test University",
            "degree": "Bachelor",
            "discipline": "Computer Science",
            "start_date": "2020-01-01",
            "end_date": "2024-01-01",
            "linkedin_profile": "https://linkedin.com/in/johndoe",
            "portfolio_website": "https://johndoe.com",
            "how_did_you_hear": "LinkedIn",
            "current_job_title": "Intern",
            "current_employer": "TechCorp",
            "skills": "Python, Django, REST",
            # Dynamic education fields.
            "school[]": ["Test University"],
            "degree[]": ["Bachelor"],
            "discipline[]": ["Computer Science"],
            "start_date[]": ["2020-01-01"],
            "end_date[]": ["2024-01-01"],
            # Dynamic work experience fields.
            "work_job_title[]": ["Software Intern"],
            "work_employer[]": ["TechCorp"],
            "work_start_date[]": ["2021-06-01"],
            "work_end_date[]": ["2021-08-01"],
            "job_description[]": ["Developed features"],
        }
        
        response = self.client.post(self.apply_url, post_data)
        
        # For non-AJAX, expect a redirect to the job detail page.
        expected_redirect = f"/job/{self.job.id}/?applied=true"
        self.assertRedirects(response, expected_redirect)
        
        # Verify an Application was created.
        application = Application.objects.get(applicant=self.applicant, job=self.job)
        self.assertEqual(application.education, [{
            "school": "Test University",
            "degree": "Bachelor",
            "discipline": "Computer Science",
            "start_date": "2020-01-01",
            "end_date": "2024-01-01"
        }])
        self.assertEqual(application.work_experience, [{
            "work_job_title": "Software Intern",
            "work_employer": "TechCorp",
            "work_start_date": "2021-06-01",
            "work_end_date": "2021-08-01",
            "job_description": "Developed features"
        }])
        
        # Verify a Candidate record was created/updated.
        from tutorials.models.candidate_models import Candidate
        candidate = Candidate.objects.get(user=self.applicant_user, job=self.job)
        self.assertEqual(candidate.first_name, "John")
        self.assertEqual(candidate.last_name, "Doe")
        self.assertEqual(candidate.phone, "1234567890")
        self.assertEqual(candidate.skills, "Python, Django, REST")
        self.assertEqual(candidate.application_status, "Pending")
        
        # Check notifications.
        from tutorials.models.notifications import EmployerNotification, ApplicantNotification
        self.assertTrue(EmployerNotification.objects.filter(employer=self.job.employer).exists())
        self.assertTrue(ApplicantNotification.objects.filter(applicant=self.applicant).exists())
        
        # Check that a success message is set.
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Your application has been submitted successfully" in m.message for m in messages))

    def test_post_valid_application_ajax(self):
        """Valid AJAX POST returns a JSON response with success."""
        self.login_applicant()
        
        post_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "applicant@example.com",
            "phone": "1234567890",
            "address": "123 Main St",
            "school": "Test University",
            "degree": "Bachelor",
            "discipline": "Computer Science",
            "start_date": "2020-01-01",
            "end_date": "2024-01-01",
            "linkedin_profile": "https://linkedin.com/in/johndoe",
            "portfolio_website": "https://johndoe.com",
            "how_did_you_hear": "LinkedIn",
            "current_job_title": "Intern",
            "current_employer": "TechCorp",
            "skills": "Python, Django, REST",
            # Dynamic education fields.
            "school[]": ["Test University"],
            "degree[]": ["Bachelor"],
            "discipline[]": ["Computer Science"],
            "start_date[]": ["2020-01-01"],
            "end_date[]": ["2024-01-01"],
            # Dynamic work experience fields.
            "work_job_title[]": ["Software Intern"],
            "work_employer[]": ["TechCorp"],
            "work_start_date[]": ["2021-06-01"],
            "work_end_date[]": ["2021-08-01"],
            "job_description[]": ["Developed features"],
        }
        
        # No files provided since we removed file fields.
        response = self.client.post(
            self.apply_url,
            post_data,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"success": True})
        
    def test_post_invalid_application(self):
        """Invalid POST submission returns errors (JSON for AJAX or re-renders the form)."""
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
        # Non-AJAX: re-render form with errors.
        response = self.client.post(self.apply_url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "applicants_application.html")
        self.assertIn("form", response.context)
        form = response.context["form"]
        self.assertFalse(form.is_valid())
        
        # AJAX: return JSON with errors.
        response_ajax = self.client.post(self.apply_url, post_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response_ajax.status_code, 200)
        json_response = response_ajax.json()
        self.assertFalse(json_response.get("success"))
        self.assertIn("error", json_response)
        
    def test_duplicate_application(self):
        """If the applicant has already applied, they should be redirected to job_detail with an error message."""
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
            "discipline": "Computer Science",
            "start_date": "2020-01-01",
            "end_date": "2024-01-01",
            "linkedin_profile": "https://linkedin.com/in/johndoe",
            "portfolio_website": "https://johndoe.com",
            "how_did_you_hear": "LinkedIn",
            "current_job_title": "Intern",
            "current_employer": "TechCorp",
            "skills": "Python, Django, REST",
            # Dynamic fields.
            "school[]": ["Test University"],
            "degree[]": ["Bachelor"],
            "discipline[]": ["Computer Science"],
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
