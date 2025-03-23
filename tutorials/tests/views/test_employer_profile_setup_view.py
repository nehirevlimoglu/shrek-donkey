from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.employer_models import Employer
from tutorials.forms.employer_forms import EmployerProfileForm
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

class EmployerProfileSetupViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='employeruser',
            password='testpass',
            role='Employer',
            email='employer@example.com'
        )
        self.profile_url = reverse('employer_profile_setup')

    def test_get_profile_setup_page_no_existing_employer(self):
        """Employer accessing profile setup without existing profile."""
        self.client.login(username='employeruser', password='testpass')

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'employer_profile_setup.html')
        self.assertIn('form', response.context)

    def test_get_profile_setup_page_existing_employer(self):
        """Employer accessing profile setup with existing profile."""
        Employer.objects.create(user=self.user, company_name='TechCorp')
        self.client.login(username='employeruser', password='testpass')

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'employer_profile_setup.html')
        self.assertContains(response, 'TechCorp')

    def test_post_valid_form_creates_employer(self):
        """Submitting valid form data creates a new Employer profile."""
        # Use the correct username.
        self.client.login(username='employeruser', password='testpass')

        valid_form_data = {
            'company_name': 'TestCorp',
            'company_website': 'https://testcorp.com',
            'industry': 'Tech',
            'company_location': 'Remote'
        }

        response = self.client.post(self.profile_url, valid_form_data)
        self.assertRedirects(response, reverse('employer_home_page'))

        employer = Employer.objects.get(user=self.user)
        self.assertEqual(employer.company_name, 'TestCorp')
        self.assertEqual(employer.company_website, 'https://testcorp.com')

    def test_post_valid_form_updates_existing_employer(self):
        """Submitting valid data updates existing Employer profile."""
        # Use the correct username.
        self.client.login(username='employeruser', password='testpass')

        existing_employer = Employer.objects.create(
            user=self.user,
            username=self.user.username,  # Set the username to match the logged-in user.
            company_name='Old Company',
            company_website='https://oldwebsite.com',
            industry='Tech',
            company_location='Old City'
        )


        update_form_data = {
            'company_name': 'Updated Company',
            'company_website': 'https://updatedwebsite.com',
            'industry': 'Finance',
            'company_location': 'New City'
        }

        response = self.client.post(self.profile_url, update_form_data)

        # Check redirection to the employer home page.
        self.assertRedirects(response, reverse('employer_home_page'))

        # Verify the employer object was updated.
        existing_employer.refresh_from_db()
        self.assertEqual(existing_employer.company_name, 'Updated Company')
        self.assertEqual(existing_employer.company_website, 'https://updatedwebsite.com')
        self.assertEqual(existing_employer.industry, 'Finance')
        self.assertEqual(existing_employer.company_location, 'New City')

    def test_redirect_if_not_logged_in(self):
        """Ensure user is redirected to login if not authenticated."""
        response = self.client.get(self.profile_url)
        self.assertRedirects(response, f'/log_in/?next={self.profile_url}')
