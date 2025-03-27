from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from tutorials.models.employer_models import (
    Employer, Job, Candidate, EmployerEvent
)

User = get_user_model()

class EmployerInterviewEventTests(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create employer user
        self.employer_user = User.objects.create_user(
            username='@testemployer',
            password='testpass123',
            email='employer@test.com',
            first_name='Test',
            last_name='Employer',
            role='Employer'
        )
        
        # Create employer profile
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username='@testemployer',
            email='employer@test.com',
            company_name='Test Company',
            company_location='Test Location',
            industry='Tech'
        )

        # Create applicant user
        self.applicant_user = User.objects.create_user(
            username='@testapplicant',
            password='testpass123',
            email='applicant@test.com',
            first_name='John',
            last_name='Doe',
            role='Applicant'
        )

        # Create a job
        self.job = Job.objects.create(
            employer=self.employer,
            title='Software Engineer',
            description='Test job description',
            location='Test Location',
            job_type='Full Time'
        )

        # Create a candidate
        self.candidate = Candidate.objects.create(
            user=self.applicant_user,
            job=self.job,
            first_name='John',
            last_name='Doe',
            application_status='Pending'
        )

        self.client = Client()
        self.client.login(username='@testemployer', password='testpass123')
        self.url = reverse('create_interview_event')

    def test_create_interview_event_success(self):
        """Test successful creation of an interview event"""
        response = self.client.post(self.url, {
            'candidate_id': self.candidate.id,
            'job_id': self.job.id
        })
        
        # Check redirect
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('employer_calendar'))

        # Check if event was created
        event = EmployerEvent.objects.latest('start')
        self.assertEqual(
            event.title,
            f"Interview - {self.candidate.first_name} ({self.job.title})"
        )
        self.assertEqual(event.employer, self.employer)

        # Check event timing
        tomorrow = timezone.now().date() + timedelta(days=1)
        self.assertEqual(event.start.date(), tomorrow)
        self.assertEqual(event.start.hour, 10)
        self.assertEqual(event.end.hour, 11)

    def test_create_interview_event_unauthorized(self):
        """Test interview creation by unauthorized user"""
        # Login as applicant instead of employer
        self.client.login(username='@testapplicant', password='testpass123')
        
        response = self.client.post(self.url, {
            'candidate_id': self.candidate.id,
            'job_id': self.job.id
        })
        
        self.assertEqual(response.status_code, 403)  # Forbidden
        self.assertEqual(EmployerEvent.objects.count(), 0)

    def test_create_interview_event_invalid_candidate(self):
        """Test interview creation with invalid candidate ID"""
        response = self.client.post(self.url, {
            'candidate_id': 99999,  # Invalid ID
            'job_id': self.job.id
        })
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(EmployerEvent.objects.count(), 0)

    def test_create_interview_event_missing_data(self):
        """Test interview creation with missing required data"""
        response = self.client.post(self.url, {})
        
        self.assertEqual(response.status_code, 400)
        self.assertEqual(EmployerEvent.objects.count(), 0)

    def test_create_interview_event_overlapping(self):
        """Test creation of overlapping interview events"""
        # Create first interview
        self.client.post(self.url, {
            'candidate_id': self.candidate.id,
            'job_id': self.job.id
        })

        # Try to create overlapping interview
        response = self.client.post(self.url, {
            'candidate_id': self.candidate.id,
            'job_id': self.job.id
        })
        
        # Should prevent overlapping interviews
        self.assertEqual(response.status_code, 400)
        self.assertEqual(EmployerEvent.objects.count(), 1)  # Only first event created

    def test_create_interview_event_updates_candidate_status(self):
        """Test that creating an interview updates candidate status"""
        self.client.post(self.url, {
            'candidate_id': self.candidate.id,
            'job_id': self.job.id
        })
        
        # Refresh candidate from database
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.application_status, 'Interview') 