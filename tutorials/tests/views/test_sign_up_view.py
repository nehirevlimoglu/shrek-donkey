from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.employer_models import Employer
from tutorials.models.applicants_models import Applicant

User = get_user_model()


class SignUpViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('sign-up')

    def test_get_signup_page(self):
        """Test GET request renders signup form"""
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up.html')
        self.assertContains(response, '<form')

    def test_successful_employer_signup_creates_employer_and_redirects(self):
        form_data = {
            'username': 'uniqueemployer123',
            'first_name': 'Employer',
            'last_name': 'User',
            'email': 'uniqueemployer123@example.com',
            'confirm_email': 'uniqueemployer123@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'role': 'Employer'
        }

        response = self.client.post(self.signup_url, form_data)

        # Ensure form errors get printed if the response isn't a redirect
        if response.status_code != 302:
            form = response.context['form']
            print("\nFORM ERRORS:", form.errors.as_json())

        self.assertRedirects(response, reverse('employer_profile_setup'))

        user = User.objects.get(username='uniqueemployer123')
        self.assertTrue(user.check_password('StrongPass123!'))
        self.assertEqual(user.role, 'Employer')

        employer = Employer.objects.get(user=user)
        self.assertEqual(employer.email, 'uniqueemployer123@example.com')
        self.assertEqual(employer.username, 'uniqueemployer123')



    def test_successful_applicant_signup_creates_applicant_and_redirects(self):
        """Valid applicant signup creates Applicant profile and redirects correctly"""
        form_data = {
            'username': 'applicantuser',
            'first_name': 'Applicant',
            'last_name': 'User',
            'email': 'applicant@example.com',
            'confirm_email': 'applicant@example.com',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
            'role': 'Applicant'
        }

        response = self.client.post(self.signup_url, form_data)

        self.assertRedirects(response, reverse('applicant_profile_setup'))

        user = User.objects.get(username='applicantuser')
        self.assertTrue(user.check_password('StrongPass123'))
        self.assertEqual(user.role, 'Applicant')

        applicant = Applicant.objects.get(user=user)
        self.assertIsNotNone(applicant)


    def test_invalid_signup_form_shows_errors(self):
        """Invalid form submission does not create user and shows errors"""
        form_data = {
            'username': '',  # invalid: username required
            'email': 'invalid-email',  # invalid: incorrect format
            'confirm_email': 'invalid-email',
            'password1': 'pass123',
            'password2': 'pass1234',  # passwords don't match
            'role': 'Employer'
        }

        response = self.client.post(self.signup_url, form_data)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up.html')

        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertContains(response, "This field is required")
        self.assertContains(response, "Enter a valid email address")
        self.assertContains(response, "Passwords do not match.")

        self.assertEqual(User.objects.count(), 0)