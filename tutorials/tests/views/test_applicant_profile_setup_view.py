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

    def test_post_valid_form_updates_existing_applicant(self):
        """
        This test updates an existing applicant.
        It includes first_name and last_name and uses the correct degree value.
        """
        existing_applicant = Applicant.objects.create(
            user=self.user,
            degree='bachelors',
            salary_preferences='50000',
            location_preferences='On-site',
        )

        self.client.login(username='@applicantuser', password='testpass')

        update_form_data = {
            'degree': 'phd',  # Use the internal value (lowercase)
            'salary_preferences': '90000',
            'location_preferences': 'Hybrid',
            'job_preferences': [self.job_title2.id],
            'cv': SimpleUploadedFile(
                "updated_resume.pdf", b"%PDF-1.4 content", content_type="application/pdf"
            ),
            'first_name': 'Jane',  # Required field
            'last_name': 'Doe',    # Required field
        }

        response = self.client.post(self.profile_url, update_form_data)
        self.assertRedirects(response, reverse('applicants-home-page'))

        existing_applicant.refresh_from_db()
        self.assertEqual(existing_applicant.degree, 'phd')
        self.assertEqual(existing_applicant.salary_preferences, '90000')
        self.assertEqual(existing_applicant.location_preferences, 'Hybrid')
        self.assertNotIn(self.job_title1, existing_applicant.job_preferences.all())
        self.assertIn(self.job_title2, existing_applicant.job_preferences.all())

    def test_post_valid_form_updates_existing_applicant_without_names(self):
        """
        If the form is submitted without first_name and last_name, it should fail.
        This test checks that these fields are required.
        """
        existing_applicant = Applicant.objects.create(
            user=self.user,
            degree='Bachelors',
            salary_preferences='50000',
            location_preferences='On-site',
        )

        self.client.login(username='@applicantuser', password='testpass')

        update_form_data = {
            'degree': 'phd',
            'salary_preferences': '90000',
            'location_preferences': 'Hybrid',
            'job_preferences': [self.job_title2.id],
            'cv': SimpleUploadedFile(
                "updated_resume.pdf", b"%PDF-1.4 content", content_type="application/pdf"
            ),
            # first_name and last_name intentionally omitted to trigger validation errors.
        }

        response = self.client.post(self.profile_url, update_form_data)
        # Since the form is invalid, there is no redirect.
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'applicant_profile_setup.html')
        form = response.context['form']
        self.assertFalse(form.is_valid())
        # Instead of checking for a specific string in the rendered HTML,
        # we assert that the form errors contain 'first_name' and 'last_name'.
        self.assertIn('first_name', form.errors)
        self.assertIn('last_name', form.errors)

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
        # Instead of asserting the literal error text, we check that errors exist for required fields.
        self.assertIn('first_name', form.errors)
        self.assertIn('last_name', form.errors)

    def test_redirect_if_not_logged_in(self):
        response = self.client.get(self.profile_url)
        self.assertRedirects(response, f'/log_in/?next={self.profile_url}')
