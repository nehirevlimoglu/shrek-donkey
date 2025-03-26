from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from tutorials.models.employer_models import Employer
from tutorials.forms.employer_forms import EmployerProfileForm
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib import messages

User = get_user_model()

class EmployerProfileTests(TestCase):
    """Test suite for employer profile editing functionality"""

    def setUp(self):
        """Set up test data"""
        # Create employer user
        self.employer_user = User.objects.create_user(
            username="test_employer",
            password="password123",
            email="employer@example.com",
            role='Employer'
        )

        # Create employer profile
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username="test_employer",
            email="employer@example.com",
            company_name="Tech Corp",
            company_location="Test Location"
        )

        self.client = Client()
        self.client.force_login(self.employer_user)

    def test_edit_company_profile_get(self):
        """Test getting the edit profile form"""
        response = self.client.get(reverse('edit_company_profile'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_company_profile.html')
        self.assertIsInstance(response.context['form'], EmployerProfileForm)
        self.assertEqual(response.context['form'].instance, self.employer)


    def test_edit_company_profile_post_invalid_data(self):
        """Test profile update with invalid data"""
        invalid_data = {
            'company_name': '',  # Company name is required
            'email': 'invalid-email'  # Invalid email format
        }

        response = self.client.post(
            reverse('edit_company_profile'),
            invalid_data
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_company_profile.html')
        self.assertFalse(response.context['form'].is_valid())
        
        # Verify no changes in database
        self.employer.refresh_from_db()
        self.assertEqual(self.employer.company_name, 'Tech Corp')

   

    