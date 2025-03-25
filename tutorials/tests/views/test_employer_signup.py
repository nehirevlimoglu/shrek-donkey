from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from tutorials.models.employer_models import Employer
from unittest.mock import patch
import json

User = get_user_model()

class EmployerSignUpViewTests(TestCase):
    """Test suite for employer signup functionality"""

    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('sign-up')
        self.valid_employer_data = {
            'username': '@newemployer',
            'email': 'employer@test.com',
            'confirm_email': 'employer@test.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'role': 'Employer',
            'first_name': 'Test',
            'last_name': 'Employer'
        }

    def test_get_signup_page(self):
        """Test GET request returns signup form"""
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up.html')
        self.assertIn('form', response.context)

    def test_successful_employer_signup(self):
        """Test successful employer registration with valid data"""
        response = self.client.post(self.signup_url, self.valid_employer_data)
        
        # Check response
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, f"{reverse('employer_home_page')}?newUser=true")
        
        # Check user creation
        user = User.objects.filter(username='@newemployer').first()
        self.assertIsNotNone(user, "User should be created")
        self.assertEqual(user.email, 'employer@test.com')
        self.assertEqual(user.role, 'Employer')
        
        # Check employer profile creation
        employer = Employer.objects.filter(user=user).first()
        self.assertIsNotNone(employer, "Employer profile should be created")
        self.assertEqual(employer.username, user.username)
        self.assertEqual(employer.email, user.email)

    def test_invalid_role_signup(self):
        """Test signup attempt with non-employer role"""
        invalid_data = self.valid_employer_data.copy()
        invalid_data['role'] = 'Applicant'
        
        response = self.client.post(self.signup_url, invalid_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up.html')
        self.assertFalse(User.objects.exists())
        self.assertEqual(
            response.context['form'].errors['role'][0],
            "Only employers can sign up here."
        )

    def test_form_validation_errors(self):
        """Test various form validation errors"""
        test_cases = [
            {
                'field': 'email',
                'value': 'not-an-email',
                'error': 'Enter a valid email address.'
            },
            {
                'field': 'username',
                'value': 'invalid',
                'error': 'Username must consist of @ followed by at least three alphanumericals'
            },
            {
                'field': 'password2',
                'value': 'different',
                'error': 'Passwords do not match.'
            }
        ]
        
        for test_case in test_cases:
            invalid_data = self.valid_employer_data.copy()
            invalid_data[test_case['field']] = test_case['value']
            
            response = self.client.post(self.signup_url, invalid_data)
            
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'sign_up.html')
            self.assertIn(test_case['field'], response.context['form'].errors)
            self.assertIn(
                test_case['error'],
                str(response.context['form'].errors[test_case['field']])
            )

    def test_employer_profile_creation_failure(self):
        """Test handling of employer profile creation failure"""
        with patch('tutorials.models.employer_models.Employer.objects.create') as mock_create:
            mock_create.side_effect = Exception("Database error")
            
            response = self.client.post(self.signup_url, self.valid_employer_data)
            
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'sign_up.html')
            self.assertFalse(User.objects.exists())
            self.assertIn(
                "Failed to create employer profile. Please try again.",
                response.context['form'].errors['__all__']
            )

    def test_missing_required_fields(self):
        """Test signup with missing required fields"""
        required_fields = ['username', 'email', 'password1', 'password2', 'role']
        
        for field in required_fields:
            invalid_data = self.valid_employer_data.copy()
            invalid_data.pop(field)
            
            response = self.client.post(self.signup_url, invalid_data)
            
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'sign_up.html')
            self.assertIn(field, response.context['form'].errors)
            self.assertIn(
                "This field is required.",
                str(response.context['form'].errors[field])
            )
            self.assertFalse(User.objects.exists())

    def test_duplicate_username(self):
        """Test signup with existing username"""
        # Create first user
        User.objects.create_user(
            username='@newemployer',
            password='testpass123',
            email='existing@test.com',
            role='Employer'
        )
        
        response = self.client.post(self.signup_url, self.valid_employer_data)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up.html')
        self.assertIn('username', response.context['form'].errors)
        self.assertIn(
            "User with this Username already exists.",
            str(response.context['form'].errors['username'])
        )

    def test_database_error_handling(self):
        """Test handling of database errors during user creation"""
        with patch('django.contrib.auth.models.User.save') as mock_save:
            mock_save.side_effect = Exception("Database error")
            
            response = self.client.post(self.signup_url, self.valid_employer_data)
            
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'sign_up.html')
            self.assertFalse(User.objects.exists())
            self.assertIn(
                "Failed to create employer profile. Please try again.",
                response.context['form'].errors['__all__']
            ) 