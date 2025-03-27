from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from tutorials.models.employer_models import Employer, Job, Candidate, Interview
from tutorials.models.user_model import User
from datetime import datetime, timedelta

class EmployerInterviewTests(TestCase):
    def setUp(self):
        # Create test user and employer
        self.client = Client()
        self.employer_user = User.objects.create_user(
            username='@testemployer',
            password='testpass123',
            email='employer@test.com',
            role='Employer'
        )
        
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username='@testemployer',
            email='employer@test.com',
            company_name='Test Company'
        )

        # Create a test job
        self.job = Job.objects.create(
            employer=self.employer,
            title='Test Job',
            description='Test Description'
        )

        # Create a test candidate
        self.candidate_user = User.objects.create_user(
            username='@testcandidate',
            password='testpass123',
            email='candidate@test.com',
            role='Applicant'
        )

        self.candidate = Candidate.objects.create(
            user=self.candidate_user,
            job=self.job,
            first_name='Test',
            last_name='Candidate'
        )

    def test_employer_calendar_view(self):
        """Test that employer can access their calendar view"""
        # Login as employer
        self.client.login(username='@testemployer', password='testpass123')
        
        # Access calendar view
        response = self.client.get(reverse('employer_calendar'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'employer_calendar.html')

    def test_schedule_interview(self):
        """Test creating a new interview"""
        self.client.login(username='@testemployer', password='testpass123')
        
        # Interview data
        interview_date = (timezone.now() + timedelta(days=1)).date()
        interview_time = '14:00'
        
        response = self.client.post(reverse('schedule_interview'), {
            'candidate': self.candidate.id,
            'job': self.job.id,
            'date': interview_date,
            'time': interview_time,
            'interview_link': 'https://meet.google.com/test',
            'notes': 'Test interview notes'
        })

        # Check if interview was created
        self.assertEqual(Interview.objects.count(), 1)
        interview = Interview.objects.first()
        self.assertEqual(interview.candidate, self.candidate)
        self.assertEqual(interview.job, self.job)

    def test_get_interviews(self):
        """Test retrieving employer's interviews"""
        self.client.login(username='@testemployer', password='testpass123')
        
        # Create a test interview
        Interview.objects.create(
            candidate=self.candidate,
            job=self.job,
            date=timezone.now().date(),
            time='15:00'
        )

        response = self.client.get(reverse('get_interviews'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()) > 0)

    def test_unauthorized_access(self):
        """Test that non-employers cannot access interview features"""
        # Create and login as non-employer user
        non_employer = User.objects.create_user(
            username='@regular',
            password='testpass123',
            email='regular@test.com',
            role='Applicant'
        )
        self.client.login(username='@regular', password='testpass123')
        
        # Try to access employer calendar
        response = self.client.get(reverse('employer_calendar'))
        self.assertEqual(response.status_code, 403)

    def test_interview_reschedule(self):
        """Test rescheduling an existing interview"""
        self.client.login(username='@testemployer', password='testpass123')
        
        # Create initial interview
        interview = Interview.objects.create(
            candidate=self.candidate,
            job=self.job,
            date=timezone.now().date(),
            time='15:00'
        )

        # New interview time
        new_date = (timezone.now() + timedelta(days=2)).date()
        new_time = '16:00'

        response = self.client.post(reverse('reschedule_interview', kwargs={'pk': interview.pk}), {
            'date': new_date,
            'time': new_time
        })

        # Refresh interview from database
        interview.refresh_from_db()
        self.assertEqual(interview.time.strftime('%H:%M'), new_time)

    def test_interview_validation(self):
        """Test interview scheduling validation"""
        self.client.login(username='@testemployer', password='testpass123')
        
        # Try to schedule interview in the past
        past_date = (timezone.now() - timedelta(days=1)).date()
        
        response = self.client.post(reverse('schedule_interview'), {
            'candidate': self.candidate.id,
            'job': self.job.id,
            'date': past_date,
            'time': '14:00'
        })

        # Should not create interview
        self.assertEqual(Interview.objects.count(), 0) 