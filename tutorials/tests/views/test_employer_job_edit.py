from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from tutorials.models.employer_models import Employer, Job
from tutorials.forms.employer_forms import JobForm
from django.utils.timezone import now, timedelta
from django.contrib.messages import get_messages

User = get_user_model()

class EmployerJobEditTests(TestCase):
    """Test suite for employer job editing functionality"""

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

        # Create a sample job
        self.job = Job.objects.create(
            employer=self.employer,
            title="Software Engineer",
            description="Test job description",
            location="Test Location",
            job_type="Full Time",
            salary="100000",
            requirements="Python, Django",
            application_deadline=now().date() + timedelta(days=30)
        )

        self.client = Client()
        self.client.force_login(self.employer_user)

    def test_job_detail_view(self):
        """Test viewing job details"""
        response = self.client.get(reverse('job_detail', args=[self.job.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'job_detail.html')
        self.assertEqual(response.context['job'], self.job)

    def test_job_detail_nonexistent_job(self):
        """Test viewing details of a non-existent job"""
        response = self.client.get(reverse('job_detail', args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_edit_nonexistent_job(self):
        """Test editing a non-existent job"""
        response = self.client.get(reverse('job_edit', args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_edit_job_view_get_form(self):
        """Test that GET request returns the correct form with job instance"""
        response = self.client.get(reverse('job_edit', args=[self.job.pk]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_job.html')
        self.assertIsInstance(response.context['form'], JobForm)
        self.assertEqual(response.context['form'].instance, self.job)
        self.assertEqual(response.context['job'], self.job)

    def test_edit_job_view_post_valid_data(self):
        """Test successful job update with valid POST data"""
        updated_data = {
            'title': 'Updated Software Engineer',
            'description': 'Updated description',
            'location': 'Updated Location',
            'job_type': 'Part Time',
            'salary': '120000',
            'requirements': 'Updated requirements',
            'application_deadline': (now().date() + timedelta(days=45)).strftime('%Y-%m-%d'),
            'company_name': 'Tech Corp',
            'position': 'Senior Developer',
            'benefits': 'Health Insurance',
            'contact_email': 'employer@example.com'
        }

        response = self.client.post(
            reverse('job_edit', args=[self.job.pk]),
            updated_data,
            follow=True
        )

        # Refresh job from database
        self.job.refresh_from_db()

        # Check that job was updated
        self.assertEqual(self.job.title, updated_data['title'])
        self.assertEqual(self.job.description, updated_data['description'])
        self.assertEqual(self.job.location, updated_data['location'])
        self.assertEqual(self.job.job_type, updated_data['job_type'])
        self.assertEqual(self.job.salary, updated_data['salary'])
        self.assertEqual(self.job.requirements, updated_data['requirements'])

        # Check redirect
        self.assertRedirects(response, reverse('employer_job_detail', args=[self.job.pk]))

    def test_edit_job_view_post_invalid_data(self):
        """Test job update with invalid POST data"""
        invalid_data = {
            'title': '',  # Title is required
            'description': 'Updated description'
        }

        response = self.client.post(
            reverse('job_edit', args=[self.job.pk]),
            invalid_data
        )

        # Check that form is invalid
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['form'].is_valid())
        self.assertTemplateUsed(response, 'edit_job.html')

        # Check that job wasn't updated
        self.job.refresh_from_db()
        self.assertEqual(self.job.title, "Software Engineer")  # Original title remains

    def test_edit_job_view_form_instance(self):
        """Test that form is initialized with correct job instance"""
        response = self.client.get(reverse('job_edit', args=[self.job.pk]))
        
        form = response.context['form']
        self.assertEqual(form.instance.id, self.job.id)
        self.assertEqual(form.instance.title, self.job.title)
        self.assertEqual(form.instance.description, self.job.description) 