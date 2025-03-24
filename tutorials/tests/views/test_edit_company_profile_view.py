from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages

from tutorials.models.employer_models import Employer
from tutorials.forms.employer_forms import EmployerProfileForm  # Adjust import if needed

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
                        'edit_company_profile.html': 'Dummy edit company profile template',
                        'error.html': 'Dummy error template: {{ message }}'
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

    def test_get_edit_company_profile_view(self):
        """Test that a GET request renders the edit company profile page with a pre-filled form."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "edit_company_profile.html")
        # Check that the form is in context and pre-populated.
        self.assertIn("form", response.context)
        form = response.context["form"]
        self.assertIsInstance(form, EmployerProfileForm)
        self.assertEqual(form.initial.get("company_name"), self.employer.company_name)

    def test_post_valid_edit_company_profile(self):
        """Test that a valid POST updates the employer profile and redirects to employer_settings."""
        # Supply the minimal fields required by EmployerProfileForm.
        valid_data = {
            "company_name": "Updated Company",
            "company_location": "Updated City",
            "industry": "Updated Industry",
            # Add any additional required fields here if necessary.
            # For example, if the form includes a file upload for 'logo', you can include:
            # "logo": SimpleUploadedFile("logo.jpg", b"dummy_content", content_type="image/jpeg"),
        }
        response = self.client.post(self.url, valid_data)
        # Expect a redirect to employer_settings.
        self.assertEqual(response.status_code, 302)
        expected_redirect = reverse("employer_settings")
        self.assertRedirects(response, expected_redirect)
        # Reload the employer and verify updates.
        self.employer.refresh_from_db()
        self.assertEqual(self.employer.company_name, "Updated Company")
        self.assertEqual(self.employer.company_location, "Updated City")
        self.assertEqual(self.employer.industry, "Updated Industry")
        # Check that a success message was added.
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Profile updated successfully" in message.message for message in messages))

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
