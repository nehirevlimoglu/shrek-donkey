from django.test import TestCase, Client
from django.urls import reverse
from tutorials.models.user_model import User
from tutorials.models.applicants_models import Applicant
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from tutorials.forms.applicants_forms import ApplicantForm
import sys
import os

class ApplicantFrontendTest(TestCase):
    """
    Advanced test suite for the Applicant frontend functionality.
    Tests complex scenarios, edge cases, and security concerns.
    """

    @classmethod
    def setUpClass(cls):
        """Set up test output formatting"""
        super().setUpClass()
        cls.maxDiff = None
        cls.verbosity = 2
        
    def setUp(self):
        """Set up test data"""
        super().setUp()
        print("\nSetting up test data...")

        self.client = Client()
        self.user = User.objects.create_user(
            username='testapplicant',
            password='testpass123',
            email='test@example.com',
            first_name='Test',
            last_name='Applicant',
            role='Applicant'
        )
        print(f"✅ Created test user: {self.user.username}")

        self.applicant = Applicant.objects.create(
            user=self.user,
            degree='Computer Science',
            salary_preferences='$50,000-$70,000',
            job_preferences='Software Development',
            location_preferences='Remote'
        )
        print(f"✅ Created applicant profile for: {self.user.username}")

        success = self.client.login(username='testapplicant', password='testpass123')
        print(f"✅ User login {'successful' if success else 'failed'}")

    def tearDown(self):
        """Clean up after each test"""
        super().tearDown()
        print("\nCleaning up test data...")
        # Clean up any uploaded files
        if hasattr(self, 'applicant') and self.applicant.cv:
            if os.path.exists(self.applicant.cv.path):
                os.remove(self.applicant.cv.path)

    def run(self, result=None):
        """Enhanced test runner with detailed output"""
        test_name = self._testMethodName
        print(f"\n{'='*80}\nRunning Test: {test_name}\n{'='*80}")
        test_method = getattr(self, test_name)
        test_doc = test_method.__doc__ or "No description provided"
        print(f"Test Description: {test_doc.strip()}\n")
        
        result = super().run(result)
        
        if hasattr(result, 'failures') and hasattr(result, 'errors'):
            if test_name in [failure[0]._testMethodName for failure in result.failures + result.errors]:
                print(f"\n❌ Test FAILED: {test_name}")
            else:
                print(f"\n✅ Test PASSED: {test_name}")
        
        return result

    def test_concurrent_profile_updates(self):
        """
        Test handling of concurrent profile updates.
        Verifies data integrity when multiple updates occur simultaneously.
        """
        # Create a second client
        client2 = Client()
        client2.login(username='testapplicant', password='testpass123')
        
        # First client updates profile
        response1 = self.client.post(
            reverse('applicants-edit-profile'),
            {
                'first_name': 'Update1',
                'last_name': 'Name1',
                'degree': 'Degree1',
                'salary_preferences': '$80,000-$100,000',
                'job_preferences': 'Job1',
                'location_preferences': 'Location1'
            }
        )
        
        # Second client updates profile immediately after
        response2 = client2.post(
            reverse('applicants-edit-profile'),
            {
                'first_name': 'Update2',
                'last_name': 'Name2',
                'degree': 'Degree2',
                'salary_preferences': '$90,000-$110,000',
                'job_preferences': 'Job2',
                'location_preferences': 'Location2'
            }
        )
        
        # Verify the latest update is saved
        updated_applicant = Applicant.objects.get(user=self.user)
        self.assertEqual(updated_applicant.degree, 'Degree2')
        self.assertEqual(updated_applicant.salary_preferences, '$90,000-$110,000')

    def test_large_file_upload(self):
        """Test handling of large CV file uploads."""
        # Create a large test file (6MB to ensure it's over the limit)
        large_file = SimpleUploadedFile(
            "large_cv.pdf",
            b'x' * (6 * 1024 * 1024),  # 6MB of data
            content_type="application/pdf"
        )
        
        # First verify the form directly
        form_data = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'degree': 'Test Degree',
            'salary_preferences': '$50,000-$70,000',
            'job_preferences': 'Software Development',
            'location_preferences': 'Remote',
        }
        form_files = {'cv': large_file}
        
        form = ApplicantForm(data=form_data, files=form_files, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('cv', form.errors)
        self.assertEqual(form.errors['cv'][0], 'File size must be under 5MB')
        
        # Now test the view
        large_file.seek(0)  # Reset file pointer
        response = self.client.post(
            reverse('applicants-edit-profile'),
            {**form_data, 'cv': large_file},
            follow=True
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'File size must be under 5MB')

    def test_xss_protection(self):
        """
        Test protection against XSS attacks.
        Verifies proper escaping of user input in profile fields.
        """
        malicious_input = '<script>alert("XSS")</script>'
        response = self.client.post(
            reverse('applicants-edit-profile'),
            {
                'first_name': malicious_input,
                'last_name': self.user.last_name,
                'degree': 'Test Degree',
                'salary_preferences': '$50,000-$70,000',
                'job_preferences': malicious_input,
                'location_preferences': 'Remote'
            },
            follow=True
        )
        
        self.assertNotContains(response, '<script>')
        self.assertContains(response, '&lt;script&gt;')

    def test_special_characters_handling(self):
        """
        Test handling of special characters in form inputs.
        Verifies proper handling of unicode and special characters.
        """
        special_chars = "Test🌟 Üser with #$@!&*()"
        response = self.client.post(
            reverse('applicants-edit-profile'),
            {
                'first_name': special_chars,
                'last_name': 'Normal',
                'degree': 'Degree with ñ and é',
                'job_preferences': '期望职位'  # Chinese characters
            }
        )
        
        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(updated_user.first_name, special_chars)

   
    def test_home_page_elements(self):
        """
        Test if home page contains all required elements.
        Verifies navigation links, user information, and dashboard components.
        """
        # Get the home page response
        response = self.client.get(reverse('applicants-home-page'))
        
        # Check if page loads successfully
        self.assertEqual(response.status_code, 200)
        
        # Verify presence of navigation elements
        self.assertContains(response, 'Home Page')
        self.assertContains(response, 'Account')
        self.assertContains(response, 'Favourites')
        self.assertContains(response, 'Applied Jobs')
        self.assertContains(response, 'Notifications')
        
        # Verify user-specific content
        self.assertContains(response, self.user.first_name)
        self.assertContains(response, self.user.last_name)

    def test_account_page_elements(self):
        """
        Test if account page displays correct user information.
        Verifies all profile fields are present and contain correct data.
        """
        # Get the account page response
        response = self.client.get(reverse('applicants-account'))
        
        # Check if page loads successfully
        self.assertEqual(response.status_code, 200)
        
        # Verify personal information
        self.assertContains(response, 'Test')  # First name
        self.assertContains(response, 'Applicant')  # Last name
        self.assertContains(response, 'test@example.com')
        
        # Verify professional information
        self.assertContains(response, 'Computer Science')
        self.assertContains(response, '$50,000-$70,000')
        self.assertContains(response, 'Software Development')
        self.assertContains(response, 'Remote')
        
        # Verify presence of edit button
        self.assertContains(response, 'Edit Profile')

    def test_edit_profile_form_display(self):
        """
        Test if edit profile form shows correct initial values.
        Verifies form pre-population with existing user data.
        """
        # Get the edit profile page response
        response = self.client.get(reverse('applicants-edit-profile'))
        
        # Check if page loads successfully
        self.assertEqual(response.status_code, 200)
        
        # Verify pre-populated personal information
        self.assertContains(response, 'Test')  # First name
        self.assertContains(response, 'Applicant')  # Last name
        
        # Verify pre-populated professional information
        self.assertContains(response, 'Computer Science')
        self.assertContains(response, '$50,000-$70,000')
        self.assertContains(response, 'Software Development')
        self.assertContains(response, 'Remote')
        
        # Verify form elements
        self.assertContains(response, 'Upload CV')
        self.assertContains(response, 'Save Changes')

    def test_edit_profile_submission(self):
        """
        Test if profile updates are saved correctly.
        Verifies form submission and database updates for all fields.
        """
        # Create a test CV file
        test_file = SimpleUploadedFile(
            "test_cv.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        
        # Submit form with updated data
        response = self.client.post(
            reverse('applicants-edit-profile'),
            {
                'first_name': 'Updated',
                'last_name': 'Name',
                'degree': 'Updated Degree',
                'cv': test_file,
                'salary_preferences': '$80,000-$100,000',
                'job_preferences': 'Full Stack Development',
                'location_preferences': 'Hybrid'
            }
        )
        
        # Verify successful redirect after submission
        self.assertEqual(response.status_code, 302)
        
        # Verify user model updates
        updated_user = User.objects.get(id=self.user.id)
        self.assertEqual(updated_user.first_name, 'Updated')
        self.assertEqual(updated_user.last_name, 'Name')
        
        # Verify applicant model updates
        updated_applicant = Applicant.objects.get(user=self.user)
        self.assertEqual(updated_applicant.degree, 'Updated Degree')
        self.assertEqual(updated_applicant.salary_preferences, '$80,000-$100,000')
        self.assertEqual(updated_applicant.job_preferences, 'Full Stack Development')
        self.assertEqual(updated_applicant.location_preferences, 'Hybrid')
        self.assertTrue(updated_applicant.cv)

    def test_invalid_form_submission(self):
        """
        Test handling of invalid form data.
        Verifies form validation and error message display.
        """
        # Submit form with invalid data
        response = self.client.post(
            reverse('applicants-edit-profile'),
            {
                'first_name': '',  # Required field left empty
                'last_name': '',   # Required field left empty
                'degree': 'Updated Degree',
            }
        )
        
        # Verify form is re-displayed
        self.assertEqual(response.status_code, 200)
        
        # Verify error message
        self.assertContains(response, 'Please fix the errors below')
        
        # Verify original data remains unchanged
        unchanged_user = User.objects.get(id=self.user.id)
        self.assertEqual(unchanged_user.first_name, 'Test')
        self.assertEqual(unchanged_user.last_name, 'Applicant')

    def test_unauthorized_access(self):
        """
        Test if non-applicants cannot access applicant pages.
        Verifies access control and permission restrictions.
        """
        # Create and login as employer
        employer = User.objects.create_user(
            username='testemployer',
            password='testpass123',
            role='Employer'
        )
        self.client.login(username='testemployer', password='testpass123')
        
        # Define protected pages
        protected_pages = [
            'applicants-home-page',
            'applicants-account',
            'applicants-edit-profile',
            'applicants-favourites',
            'applicants-applied-jobs',
            'applicants-notifications'
        ]
        
        # Test access to each protected page
        for page in protected_pages:
            response = self.client.get(reverse(page))
            self.assertEqual(
                response.status_code, 
                404,
                f"Employer should not access {page}"
            )

    def test_navigation_links(self):
        """
        Test if all navigation links are present and functional.
        Verifies proper routing and link accessibility.
        """
        # Get home page response
        response = self.client.get(reverse('applicants-home-page'))
        
        # Verify presence of navigation URLs
        self.assertContains(response, reverse('applicants-home-page'))
        self.assertContains(response, reverse('applicants-account'))
        self.assertContains(response, reverse('applicants-favourites'))
        self.assertContains(response, reverse('applicants-applied-jobs'))
        self.assertContains(response, reverse('applicants-notifications'))

    def test_applicant_stats_display(self):
        """
        Test if applicant dashboard shows correct stats.
        Verifies display of job-related statistics.
        """
        # Get home page response
        response = self.client.get(reverse('applicants-home-page'))
        
        # Verify presence of statistics sections
        self.assertContains(response, 'Total Job Listings')
        self.assertContains(response, 'Favourited Jobs')
        self.assertContains(response, 'Applications Sent')

    def test_session_handling(self):
        """Test session handling and timeout behavior."""
        # First verify we can access the page when logged in
        response = self.client.get(reverse('applicants-account'))
        self.assertEqual(response.status_code, 200)  # Should be able to access when logged in
        
        # Logout
        self.client.logout()
        
        # Try to access protected page after logout
        response = self.client.get(reverse('applicants-account'), follow=True)
        self.assertRedirects(response, '/login/?next=' + reverse('applicants-account')) 

    def test_cv_invalid_file_type(self):
        """Test rejection of invalid CV file types."""
        form_data = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'degree': 'Test Degree',
            'salary_preferences': '$50,000-$70,000',
            'job_preferences': 'Software Development',
            'location_preferences': 'Remote',
        }

        invalid_file = SimpleUploadedFile(
            "test.exe",
            b"invalid content",
            content_type="application/x-msdownload"
        )
        form = ApplicantForm(data=form_data, files={'cv': invalid_file}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['cv'][0], 'Only PDF and Word documents are allowed')

    def test_cv_file_too_large(self):
        """Test rejection of CV files exceeding size limit."""
        form_data = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'degree': 'Test Degree',
            'salary_preferences': '$50,000-$70,000',
            'job_preferences': 'Software Development',
            'location_preferences': 'Remote',
        }

        large_file = SimpleUploadedFile(
            "large.pdf",
            b'x' * (6 * 1024 * 1024),  # 6MB
            content_type="application/pdf"
        )
        form = ApplicantForm(data=form_data, files={'cv': large_file}, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertEqual(form.errors['cv'][0], 'File size must be under 5MB')

    def test_cv_valid_pdf(self):
        """Test acceptance of valid PDF CV file."""
        form_data = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'degree': 'Test Degree',
            'salary_preferences': '$50,000-$70,000',
            'job_preferences': 'Software Development',
            'location_preferences': 'Remote',
        }

        valid_pdf = SimpleUploadedFile(
            "test.pdf",
            b"valid content",
            content_type="application/pdf"
        )
        form = ApplicantForm(data=form_data, files={'cv': valid_pdf}, user=self.user)
        self.assertTrue(form.is_valid())

    def test_cv_valid_word_doc(self):
        """Test acceptance of valid Word document CV file."""
        form_data = {
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'degree': 'Test Degree',
            'salary_preferences': '$50,000-$70,000',
            'job_preferences': 'Software Development',
            'location_preferences': 'Remote',
        }

        valid_doc = SimpleUploadedFile(
            "test.doc",
            b"valid content",
            content_type="application/msword"
        )
        form = ApplicantForm(data=form_data, files={'cv': valid_doc}, user=self.user)
        self.assertTrue(form.is_valid()) 