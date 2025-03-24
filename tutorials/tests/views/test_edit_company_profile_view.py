from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from unittest.mock import patch

from tutorials.models.employer_models import Employer
from tutorials.forms.employer_forms import EmployerProfileForm  # Adjust import if needed
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

User = get_user_model()

@override_settings(
    TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': False,
        'OPTIONS': {
            'loaders': [
                (
                    'django.template.loaders.locmem.Loader',
                    {
                        'log_in.html': 'Dummy login template content',
                        'edit_company_profile.html': 'Dummy edit company profile template: {{ form.as_p }}',
                        'error.html': 'Dummy error template: {{ message }}',
                        'employer_settings.html': 'Dummy employer settings page',
                    }
                )
            ],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    }]
)

class EditCompanyProfileViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an employer user.
        self.employer_user = User.objects.create_user(
            username="employeruser",
            email="employer@example.com",
            password="password123",
            role="Employer"
        )
        self.client.force_login(self.employer_user)
        # Create an Employer instance linked to the user.
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username="employeruser",  # must match request.user.username
            email="employer@example.com",
            company_name="Original Company",
            company_location="Original City",
            industry="Tech"
        )
        self.url = reverse("edit_company_profile")

    @patch("tutorials.forms.employer_forms.EmployerProfileForm.is_valid", return_value=True)
    @patch("tutorials.forms.employer_forms.EmployerProfileForm.save")
    def test_post_valid_edit_company_profile(self, mock_save, mock_is_valid):
        """Test that a valid POST updates the employer profile and redirects to employer_settings."""
        valid_data = {
            "company_name": "Updated Company",
            "company_location": "Updated City",
            "industry": "Updated Industry",
            # If your form requires a file upload for 'logo', include a dummy file:
            "logo": SimpleUploadedFile("logo.jpg", b"dummy image content", content_type="image/jpeg"),
        }
        response = self.client.post(self.url, valid_data)
        # Now, because is_valid() is patched to True, the view should redirect.
        self.assertEqual(response.status_code, 302)
        expected_redirect = reverse("employer_settings")
        self.assertRedirects(response, expected_redirect)
        # Refresh the employer from the database.
        self.employer.refresh_from_db()
        self.assertEqual(self.employer.company_name, "Updated Company")
        self.assertEqual(self.employer.company_location, "Updated City")
        self.assertEqual(self.employer.industry, "Updated Industry")
        # Check that a success message was added.
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Profile updated successfully" in message.message for message in messages))

    def test_post_valid_edit_company_profile(self):
        self.client.login(username='@testemployer', password='testpass123')

        form_data = {
            'company_name': 'Updated Company Name',
            'company_location': 'Updated City',
            'industry': 'Tech',
            # include all other required fields used in your EmployerProfileForm
        }

        response = self.client.post(reverse('edit_company_profile'), form_data)

        if response.status_code != 302:
            print("❌ FORM ERRORS:", response.context['form'].errors)

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('employer_settings'))

        # Optional: confirm model was updated
        self.employer.refresh_from_db()
        self.assertEqual(self.employer.company_name, 'Updated Company Name')

    def test_post_invalid_edit_company_profile(self):
        """Test that an invalid POST (e.g., missing required company_name) re-renders the form with errors."""
        invalid_data = {
            "company_name": "",  # required field left blank
            "company_location": "Updated City",
            "industry": "Updated Industry",
        }
        response = self.client.post(self.url, invalid_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_company_profile.html")
        form = response.context.get("form")
        self.assertTrue(form.errors)

    def test_employer_not_found(self):
        """Test that if no Employer instance exists for the logged-in user, the error template is rendered."""
        # Delete the Employer instance.
        self.employer.delete()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "error.html")
        self.assertIn("Employer not found", response.content.decode())

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)
