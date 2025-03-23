from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.messages import get_messages
from tutorials.models.applicants_models import Applicant
from tutorials.forms.applicants_forms import ApplicantForm
from tutorials.models.employer_models import JobTitle

User = get_user_model()

class ApplicantProfileTests(TestCase):
    """
    Test suite for applicant profile management functionality.
    Tests profile viewing and editing features.
    """
    
    def setUp(self):
        """Set up test data for profile management tests"""
        # Create applicant user with first and last name.
        self.user = User.objects.create_user(
            username='@testapplicant',
            password='testpass123',
            email='test@example.com',
            first_name='Test',
            last_name='Applicant',
            role='Applicant'
        )
        
        # Create job title for M2M relationships.
        self.job_title = JobTitle.objects.create(title="Software Development")
        
        # Create applicant profile with a valid degree value.
        self.applicant = Applicant.objects.create(
            user=self.user,
            degree='bachelors',  # Valid degree choice.
            salary_preferences='50000-70000',
            location_preferences='Remote'
        )
        # Add job preferences.
        self.applicant.job_preferences.add(self.job_title)
        
        self.client = Client()
        self.client.login(username='@testapplicant', password='testpass123')
        
    def test_view_profile_authenticated(self):
        """Test that authenticated applicant can view their profile"""
        response = self.client.get(reverse('applicants-account'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'applicants_account.html')
        self.assertEqual(response.context['applicant'], self.applicant)
        self.assertEqual(response.context['user'], self.user)

    def test_edit_profile_get(self):
        """Test profile edit form display"""
        response = self.client.get(reverse('applicants-edit-profile'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'applicants_edit_profile.html')
        self.assertIsInstance(response.context['form'], ApplicantForm)
        self.assertEqual(response.context['applicant'], self.applicant)

    def test_edit_profile_invalid_data(self):
        """Test profile update with invalid data"""
        # Submit empty form.
        response = self.client.post(reverse('applicants-edit-profile'), {})
        
        self.assertEqual(response.status_code, 200)  # Form re-renders.
        self.assertTrue(response.context['form'].errors)  # Form has errors.
        
        # Check error message.
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Please fix the errors below.")

    def test_edit_profile_non_applicant(self):
        """Test that non-applicant users cannot access profile editing"""
        # Create non-applicant user.
        non_applicant = User.objects.create_user(
            username='@testemployer',
            password='testpass123',
            role='Employer'
        )
        
        self.client.login(username='@testemployer', password='testpass123')
        response = self.client.get(reverse('applicants-edit-profile'))
        
        # Should be forbidden for non-applicants.
        self.assertEqual(response.status_code, 403)

    def test_edit_profile_with_invalid_file_type(self):
        """Test uploading invalid file type for CV"""
        invalid_file = SimpleUploadedFile(
            "test_cv.txt",
            b"invalid file content",
            content_type="text/plain"
        )
        
        response = self.client.post(
            reverse('applicants-edit-profile'),
            {
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'degree': self.applicant.degree,  # 'bachelors'
                'cv': invalid_file,
                'salary_preferences': self.applicant.salary_preferences,
                'job_preferences': [self.job_title.id],
                'location_preferences': self.applicant.location_preferences
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('cv', response.context['form'].errors)

    def test_edit_profile_large_file(self):
        """Test uploading too large CV file"""
        # Create large file content (5MB+)
        large_content = b"x" * (5 * 1024 * 1024 + 1)
        large_file = SimpleUploadedFile(
            "large_cv.pdf",
            large_content,
            content_type="application/pdf"
        )
        
        response = self.client.post(
            reverse('applicants-edit-profile'),
            {
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'degree': self.applicant.degree,  # 'bachelors'
                'cv': large_file,
                'salary_preferences': self.applicant.salary_preferences,
                'job_preferences': [self.job_title.id],
                'location_preferences': self.applicant.location_preferences
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('cv', response.context['form'].errors)

    def test_edit_profile_successful_update(self):
        """Test successful profile update with all required fields"""
        response = self.client.post(
            reverse('applicants-edit-profile'),
            {
                'first_name': 'Updated',
                'last_name': 'Name',
                'degree': 'phd',  # Valid degree value.
                'salary_preferences': '80000-100000',
                'job_preferences': [self.job_title.id],
                'location_preferences': 'Hybrid'
            },
            follow=True  # Follow redirects.
        )
        
        # Check response after redirect.
        self.assertEqual(response.status_code, 200)
        
        # Check success message.
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Your changes have been saved.")
        
        # Refresh from database.
        self.applicant.refresh_from_db()
        self.user.refresh_from_db()
        
        # Check updated values.
        self.assertEqual(self.applicant.degree, 'phd')
        self.assertEqual(self.applicant.salary_preferences, '80000-100000')
        self.assertEqual(
            set(self.applicant.job_preferences.values_list('id', flat=True)),
            {self.job_title.id}
        )
        self.assertEqual(self.applicant.location_preferences, 'Hybrid')
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')

    def test_edit_profile_form_initial_values(self):
        """Test that form is populated with current user and applicant data"""
        response = self.client.get(reverse('applicants-edit-profile'))
        form = response.context['form']
        
        self.assertEqual(form.initial['degree'], self.applicant.degree)
        self.assertEqual(form.initial['salary_preferences'], self.applicant.salary_preferences)
        
        # Convert JobTitle objects to IDs in form initial data.
        actual_ids = {obj.id for obj in form.initial['job_preferences']}
        expected_ids = set(self.applicant.job_preferences.values_list('id', flat=True))
        self.assertEqual(actual_ids, expected_ids)
        
        self.assertEqual(form.initial['location_preferences'], self.applicant.location_preferences)

    def test_edit_profile_valid_cv_upload(self):
        """Test successful CV file upload"""
        cv_file = SimpleUploadedFile(
            "test_cv.pdf",
            b"%PDF-1.4\n Sample PDF content",
            content_type="application/pdf"
        )
        
        response = self.client.post(
            reverse('applicants-edit-profile'),
            {
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'degree': self.applicant.degree,  # 'bachelors'
                'cv': cv_file,
                'salary_preferences': self.applicant.salary_preferences,
                'job_preferences': [self.job_title.id],
                'location_preferences': self.applicant.location_preferences
            },
            format='multipart'
        )
        
        # Should redirect on success.
        self.assertEqual(response.status_code, 302)
        
        # Follow the redirect.
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        
        # Check success message.
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Your changes have been saved.")
        
        # Verify file was uploaded.
        self.applicant.refresh_from_db()
        self.assertTrue(self.applicant.cv)
        self.assertTrue(self.applicant.cv.name.startswith('uploads/cv/'))
        self.assertTrue(self.applicant.cv.name.endswith('.pdf'))

    def test_edit_profile_valid_doc_upload(self):
        """Test successful Word (.doc) CV upload"""
        doc_file = SimpleUploadedFile(
            "test_cv.doc",
            b"Word document content",
            content_type="application/msword"
        )
        
        response = self.client.post(
            reverse('applicants-edit-profile'),
            {
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'degree': self.applicant.degree,  # 'bachelors'
                'cv': doc_file,
                'salary_preferences': self.applicant.salary_preferences,
                'job_preferences': [str(self.job_title.id)],
                'location_preferences': self.applicant.location_preferences
            },
            format='multipart'
        )
        
        self.assertEqual(response.status_code, 302)
        
        # Follow the redirect.
        response = self.client.get(response.url)
        self.assertEqual(response.status_code, 200)
        
        # Check success message.
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Your changes have been saved.")
        
        self.applicant.refresh_from_db()
        self.assertTrue(self.applicant.cv)
        self.assertTrue(self.applicant.cv.name.startswith('uploads/cv/'))
        self.assertTrue(self.applicant.cv.name.endswith('.doc'))

    def test_edit_profile_valid_docx_upload(self):
        """Test successful Word (.docx) CV upload"""
        docx_file = SimpleUploadedFile(
            "test_cv.docx",
            b"PK\x03\x04\x14\x00\x00\x00\x00\x00" + b"Sample Word content",
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        
        response = self.client.post(
            reverse('applicants-edit-profile'),
            {
                'first_name': self.user.first_name,
                'last_name': self.user.last_name,
                'degree': self.applicant.degree,  # 'bachelors'
                'cv': docx_file,
                'salary_preferences': self.applicant.salary_preferences,
                'job_preferences': [self.job_title.id],
                'location_preferences': self.applicant.location_preferences
            },
            format='multipart',
            follow=True  # Follow redirects.
        )
        
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Your changes have been saved.")
        
        self.applicant.refresh_from_db()
        self.assertTrue(self.applicant.cv)
        self.assertTrue(self.applicant.cv.name.startswith('uploads/cv/'))
        self.assertTrue(self.applicant.cv.name.endswith('.docx'))

