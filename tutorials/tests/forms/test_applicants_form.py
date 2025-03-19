# tutorials/tests/forms/test_applicants_form.py

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from tutorials.forms.applicants_forms import ApplicantForm, ApplicationForm
from tutorials.models.applicants_models import Applicant, Application
from tutorials.models.employer_models import JobTitle, Job  # Adjust if "Job" is in a different module


class ApplicantFormTest(TestCase):
    def setUp(self):
        User = get_user_model()

        # Create a user + an Applicant instance so we have a user foreign key
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword',
            first_name='John',
            last_name='Doe',
            email='john@example.com'
        )
        self.applicant = Applicant.objects.create(
            user=self.user,
            degree='Existing Degree',
        )

        # One job title for multiple choice
        self.job_title = JobTitle.objects.create(title="Software Engineer")

        # Minimal valid form data for the ApplicantForm
        self.valid_form_data = {
            'degree': 'B.Sc. Computer Science',
            'salary_preferences': '60000',
            'location_preferences': 'Remote',

            # Because they're marked required=True in the form:
            'first_name': 'Marty',
            'last_name': 'McFly',
        }

    def test_applicant_form_prepopulate_user_fields(self):
        """
        If we initialize the form with user=..., 
        ensure the 'initial' is set for first_name & last_name.
        """
        form = ApplicantForm(user=self.user, instance=self.applicant)
        self.assertEqual(form.fields['first_name'].initial, 'John')
        self.assertEqual(form.fields['last_name'].initial, 'Doe')

    def test_applicant_form_valid_cv(self):
        """Test form validation with a valid PDF file (under size limit)."""
        fake_pdf = SimpleUploadedFile(
            "test_resume.pdf",
            b"%PDF-1.4 Fake PDF content",
            content_type="application/pdf"
        )
        data = self.valid_form_data.copy()
        files = {'cv': fake_pdf}

        form = ApplicantForm(data=data, files=files, instance=self.applicant, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)

    def test_applicant_form_invalid_cv_type(self):
        """Test form fails validation when file type is not allowed."""
        fake_txt = SimpleUploadedFile(
            "test_resume.txt",
            b"This is a test text file.",
            content_type="text/plain"
        )
        data = self.valid_form_data.copy()
        files = {'cv': fake_txt}

        form = ApplicantForm(data=data, files=files, instance=self.applicant, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('cv', form.errors)

    def test_applicant_form_invalid_cv_size(self):
        """Test form fails if the file exceeds the 5MB limit."""
        large_content = b"%PDF-1.4" + b"A" * (5 * 1024 * 1024 + 1)
        large_pdf = SimpleUploadedFile(
            "large_resume.pdf",
            large_content,
            content_type="application/pdf"
        )
        data = self.valid_form_data.copy()
        files = {'cv': large_pdf}

        form = ApplicantForm(data=data, files=files, instance=self.applicant, user=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('cv', form.errors)

    def test_applicant_form_job_preferences(self):
        """
        Ensure user can choose multiple job preferences, 
        but also must provide first_name/last_name because they're required.
        """
        data = self.valid_form_data.copy()
        data['job_preferences'] = [self.job_title.id]
        form = ApplicantForm(data=data, instance=self.applicant, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        applicant = form.save(commit=False)
        self.assertIsNotNone(applicant)

    def test_applicant_form_save_updates_user(self):
        """
        Ensure that saving the form updates the linked User's first_name, last_name.
        """
        data = self.valid_form_data.copy()
        data["first_name"] = "Alice"
        data["last_name"] = "Smith"

        form = ApplicantForm(data=data, instance=self.applicant, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)

        applicant = form.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Alice")
        self.assertEqual(self.user.last_name, "Smith")
        self.assertEqual(applicant.user, self.user)


class ApplicationFormTest(TestCase):
    def setUp(self):
        User = get_user_model()

        # A user + applicant
        self.user = User.objects.create_user(
            username='applicantuser',
            password='testpassword',
            first_name='AppFirst',
            last_name='AppLast',
            email='applicant@example.com'
        )
        self.applicant = Applicant.objects.create(
            user=self.user,
            degree='Some Degree',
        )

        self.job = Job.objects.create(
            title='Junior Developer',
            company_name='TestCo',
            location='Test City',
            salary=50000,
            description='Test job description',
        )

        self.valid_application_data = {
            "first_name": "Alice",
            "last_name": "Tester",
            "phone": "555-1234",
            "email": "alice@example.com",
            "address": "123 Test Street",
            "how_did_you_hear": "linkedin",
            "sponsorship_needed": "no",
            "confirm_information": True,
        }

    def test_application_form_valid_pdf_resume(self):
        fake_pdf = SimpleUploadedFile(
            "resume.pdf",
            b"%PDF-1.4 PDF mock content",
            content_type="application/pdf"
        )
        data = self.valid_application_data.copy()
        files = {'resume': fake_pdf}

        form = ApplicationForm(data=data, files=files)
        self.assertTrue(form.is_valid(), form.errors)

        # Because Application has a NOT NULL job_id and applicant_id, set them:
        application = form.save(commit=False)
        application.applicant = self.applicant
        application.job = self.job
        application.save()

        self.assertIsNotNone(application.pk)
        self.assertEqual(application.applicant, self.applicant)
        self.assertEqual(application.job, self.job)

    def test_application_form_cover_letter_optional(self):
        fake_pdf = SimpleUploadedFile(
            "resume.pdf",
            b"%PDF-1.4 PDF mock content",
            content_type="application/pdf"
        )
        data = self.valid_application_data.copy()
        files = {'resume': fake_pdf}

        form = ApplicationForm(data=data, files=files)
        self.assertTrue(form.is_valid(), form.errors)

        application = form.save(commit=False)
        application.applicant = self.applicant
        application.job = self.job
        application.save()
        self.assertIsNotNone(application.pk)

    def test_application_form_non_pdf_resume(self):
        fake_txt = SimpleUploadedFile(
            "resume.txt",
            b"This is a plain text file.",
            content_type="text/plain"
        )
        data = self.valid_application_data.copy()
        files = {'resume': fake_txt}

        form = ApplicationForm(data=data, files=files)
        self.assertFalse(form.is_valid())
        self.assertIn('resume', form.errors)

    def test_application_form_missing_required_field(self):
        fake_pdf = SimpleUploadedFile(
            "resume.pdf",
            b"%PDF-1.4 PDF mock content",
            content_type="application/pdf"
        )
        data = self.valid_application_data.copy()
        data.pop("email")  

        files = {'resume': fake_pdf}
        form = ApplicationForm(data=data, files=files)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_application_form_confirmation_needed(self):
        fake_pdf = SimpleUploadedFile(
            "resume.pdf",
            b"%PDF-1.4 PDF mock content",
            content_type="application/pdf"
        )
        data = self.valid_application_data.copy()
        data["confirm_information"] = False

        files = {'resume': fake_pdf}
        form = ApplicationForm(data=data, files=files)
        self.assertFalse(form.is_valid())
        self.assertIn('confirm_information', form.errors)

    def test_application_form_save(self):
        """
        Test saving a valid ApplicationForm instance with required foreign keys.
        """
        fake_pdf = SimpleUploadedFile(
            "resume.pdf",
            b"%PDF-1.4 PDF mock content",
            content_type="application/pdf"
        )
        data = self.valid_application_data.copy()
        files = {'resume': fake_pdf}

        form = ApplicationForm(data=data, files=files)
        self.assertTrue(form.is_valid(), form.errors)

        application = form.save(commit=False)
        application.applicant = self.applicant  
        application.job = self.job             
        application.save()

        self.assertIsNotNone(application.pk)
        self.assertEqual(application.first_name, "Alice")
        self.assertEqual(application.last_name, "Tester")
    
        self.assertIn("resume.pdf", application.resume.name)
    
        self.assertEqual(application.applicant, self.applicant)
        self.assertEqual(application.job, self.job)
