from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from tutorials.models.applicants_models import Applicant
from tutorials.models.employer_models import JobTitle

User = get_user_model()

class ApplicantProfileSetupTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='@applicantuser',
            password='testpass',
            role='Applicant',
            email='applicant@example.com'
        )

        # Job Titles for M2M relationships
        self.job_title1 = JobTitle.objects.create(title='Developer')
        self.job_title2 = JobTitle.objects.create(title='Designer')

        self.profile_url = reverse('applicant_profile_setup')


    def test_get_profile_setup_page_no_existing_profile(self):
        self.client.login(username='@applicantuser', password='testpass')
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'applicant_profile_setup.html')
        self.assertContains(response, '<form')
        self.assertIn('form', response.context)

    def test_get_profile_setup_page_existing_profile(self):
        Applicant.objects.create(user=self.user, degree='Bachelors')

        self.client.login(username='@applicantuser', password='testpass')
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'applicant_profile_setup.html')
        self.assertContains(response, 'Bachelors')

    def test_post_valid_form_creates_applicant(self):
        """Submitting valid form data creates a new Applicant profile."""
        self.client.login(username='@applicantuser', password='testpass')

        valid_cv = SimpleUploadedFile(
            "test_cv.pdf", 
            b"%PDF-1.4 mock pdf content", 
            content_type="application/pdf"
        )

        valid_form_data = {
            'degree': 'Masters',
            'salary_preferences': '70000',
            'location_preferences': 'Remote',
            'first_name': 'Alice',
            'last_name': 'Smith',
            'job_preferences': [self.job_title1.id, self.job_title2.id],
        }

        response = self.client.post(
            self.profile_url, 
            {**valid_form_data, 'cv': valid_cv}
        )

        self.assertRedirects(response, reverse('applicants-home-page'))

        applicant = Applicant.objects.get(user=self.user)
        self.assertEqual(applicant.degree, 'Masters')
        self.assertEqual(applicant.salary_preferences, '70000')
        self.assertEqual(applicant.location_preferences, 'Remote')
        self.assertIn(self.job_title1, applicant.job_preferences.all())
        self.assertIn(self.job_title2, applicant.job_preferences.all())

    def test_post_invalid_form_shows_errors(self):
        self.client.login(username='@applicantuser', password='testpass')

        invalid_form_data = {
            'degree': '',
            'salary_preferences': 'NotANumber',
            'location_preferences': 'Remote',
            'first_name': '',
            'last_name': '',
        }

        response = self.client.post(self.profile_url, invalid_form_data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'applicant_profile_setup.html')

        form = response.context['form']
        self.assertFalse(form.is_valid())

        self.assertContains(response, "This field is required")

    def test_post_valid_form_updates_existing_applicant(self):
        existing_applicant = Applicant.objects.create(
            user=self.user,
            degree='Bachelors',
            salary_preferences='50000',
            location_preferences='On-site',
        )

        self.client.login(username='@applicantuser', password='testpass')

        update_form_data = {
            'degree': 'PhD',
            'salary_preferences': '90000',
            'location_preferences': 'Hybrid',
            'first_name': 'Bob',
            'last_name': 'Brown',
            'job_preferences': [self.job_title2.id],
            'cv': SimpleUploadedFile(
                "updated_resume.pdf", b"%PDF-1.4", content_type="application/pdf"
            ),
        }

        response = self.client.post(self.profile_url, update_form_data)

        self.assertRedirects(response, reverse('applicants-home-page'))

        existing_applicant.refresh_from_db()
        self.assertEqual(existing_applicant.degree, 'PhD')
        self.assertEqual(existing_applicant.salary_preferences, '90000')
        self.assertEqual(existing_applicant.location_preferences, 'Hybrid')
        self.assertNotIn(self.job_title1, existing_applicant.job_preferences.all())
        self.assertIn(self.job_title2, existing_applicant.job_preferences.all())

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.profile_url)
        self.assertRedirects(response, f'/log_in/?next={self.profile_url}')