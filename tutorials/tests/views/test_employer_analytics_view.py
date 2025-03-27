from django.test import TestCase, Client
from django.urls import reverse
from django.utils.timezone import now, timedelta
from django.contrib.auth import get_user_model
from tutorials.models.employer_models import (
    Employer, Job, Candidate, Interview, EmployerNotification
)
import json
from django.db.models import Count, Q

User = get_user_model()

class EmployerAnalyticsViewTests(TestCase):
    """Test suite for employer analytics view"""

    def setUp(self):
        """Set up test data for analytics tests"""
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
            company_name="Tech Corp"
        )

        # Create multiple jobs with different statuses
        self.job1 = Job.objects.create(
            employer=self.employer,
            title="Software Engineer",
            description="Job 1 description",
            application_deadline=now().date() + timedelta(days=10)
        )

        self.job2 = Job.objects.create(
            employer=self.employer,
            title="Data Scientist",
            description="Job 2 description",
            application_deadline=now().date() + timedelta(days=15)
        )

        # Create multiple candidates with different statuses
        self.create_test_candidates()
        
        # Create some interviews
        self.create_test_interviews()

        self.client = Client()
        self.client.force_login(self.employer_user)

    def create_test_candidates(self):
        """Helper method to create test candidates with different statuses"""
        # Candidates for Job 1
        for i in range(3):
            user = User.objects.create_user(
                username=f"applicant{i}",
                email=f"applicant{i}@test.com",
                password="testpass123",
                role='Applicant'
            )
            Candidate.objects.create(
                user=user,
                job=self.job1,
                first_name=f"First{i}",
                last_name=f"Last{i}",
                application_date=now(),
                application_status="Pending"
            )

        # Create a hired candidate for Job 1
        hired_user = User.objects.create_user(
            username="hired_applicant",
            email="hired@test.com",
            password="testpass123",
            role='Applicant'
        )
        Candidate.objects.create(
            user=hired_user,
            job=self.job1,
            first_name="Hired",
            last_name="Candidate",
            application_date=now(),
            application_status="Hired"
        )

        # Candidates for Job 2
        for i in range(2):
            user = User.objects.create_user(
                username=f"job2_applicant{i}",
                email=f"job2_applicant{i}@test.com",
                password="testpass123",
                role='Applicant'
            )
            Candidate.objects.create(
                user=user,
                job=self.job2,
                first_name=f"Job2First{i}",
                last_name=f"Job2Last{i}",
                application_date=now(),
                application_status="Pending"
            )

    def create_test_interviews(self):
        """Helper method to create test interviews"""
        # Create future interviews
        Interview.objects.create(
            job=self.job1,
            candidate=Candidate.objects.filter(job=self.job1).first(),
            date=now().date() + timedelta(days=2),
            time="14:00:00"
        )
        Interview.objects.create(
            job=self.job2,
            candidate=Candidate.objects.filter(job=self.job2).first(),
            date=now().date() + timedelta(days=3),
            time="15:00:00"
        )

        # Create past interview
        Interview.objects.create(
            job=self.job1,
            candidate=Candidate.objects.filter(job=self.job1).last(),
            date=now().date() - timedelta(days=1),
            time="10:00:00"
        )

    def test_employer_not_found(self):
        """Test handling of non-existent employer profile"""
        non_employer = User.objects.create_user(
            username="non_employer",
            password="testpass123",
            email="non@test.com"
        )
        self.client.force_login(non_employer)
        
        response = self.client.get(reverse('employer_analytics'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue('error' in response.context)
        self.assertEqual(response.context['error'], 'Employer profile not found')

    def test_analytics_data(self):
        """Test that analytics data is correctly calculated and returned"""
        response = self.client.get(reverse('employer_analytics'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'employer_analytics.html')
        
        # Verify context data
        self.assertIn('total_jobs', response.context)
        self.assertIn('total_applicants', response.context)
        self.assertIn('job_analytics', response.context)
        self.assertIn('job_titles', response.context)
        self.assertIn('job_applicants', response.context)
        self.assertIn('job_interviews', response.context)
        
        # Verify the job analytics data
        job_analytics = response.context['job_analytics']
        self.assertEqual(len(job_analytics), 2)  # Should have data for both jobs
        
        # Verify JSON data
        job_titles = json.loads(response.context['job_titles'])
        job_applicants = json.loads(response.context['job_applicants'])
        job_interviews = json.loads(response.context['job_interviews'])
        
        self.assertEqual(len(job_titles), 2)
        self.assertEqual(len(job_applicants), 2)
        self.assertEqual(len(job_interviews), 2)

    def test_empty_analytics(self):
        """Test analytics display for employer with no data"""
        # Create new employer with no jobs/candidates
        empty_employer_user = User.objects.create_user(
            username="empty_employer",
            password="testpass123",
            email="empty@test.com",
            role='Employer'
        )
        empty_employer = Employer.objects.create(
            user=empty_employer_user,
            username="empty_employer",
            email="empty@test.com",
            company_name="Empty Corp"
        )
        
        self.client.force_login(empty_employer_user)
        response = self.client.get(reverse('employer_analytics'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_jobs'], 0)
        self.assertEqual(response.context['total_applicants'], 0)
        self.assertEqual(response.context['pending_interviews'], 0)
        self.assertEqual(response.context['average_apps_per_job'], 0)
        self.assertEqual(len(response.context['job_analytics']), 0)
        
        # Test JSON data
        self.assertEqual(json.loads(response.context['job_titles']), [])
        self.assertEqual(json.loads(response.context['job_applicants']), [])
        self.assertEqual(json.loads(response.context['job_interviews']), [])

    
    def test_job_analytics_data_structure(self):
        """Test that job analytics data is correctly structured"""
        response = self.client.get(reverse('employer_analytics'))
        
        job_analytics = response.context['job_analytics']
        
        # Test each job's data structure
        for job_data in job_analytics:
            self.assertIn('title', job_data)
            self.assertIn('applicants', job_data)
            self.assertIn('interviews', job_data)
            self.assertIn('hires', job_data)
            
        # Test that the lists are properly populated
        job_titles = json.loads(response.context['job_titles'])
        job_applicants = json.loads(response.context['job_applicants'])
        job_interviews = json.loads(response.context['job_interviews'])
        
        # Verify the data matches our test setup
        self.assertIn("Software Engineer", job_titles)
        self.assertIn("Data Scientist", job_titles)
        
        # Verify the lengths match
        self.assertEqual(len(job_titles), len(job_applicants))
        self.assertEqual(len(job_titles), len(job_interviews))

    def test_analytics_edge_cases(self):
        """Test analytics with edge cases like empty jobs and no applicants"""
        # Clear existing data
        Job.objects.all().delete()
        Candidate.objects.all().delete()
        Interview.objects.all().delete()
        
        response = self.client.get(reverse('employer_analytics'))
        
        # Should still return successfully
        self.assertEqual(response.status_code, 200)
        
        # Lists should be empty but present
        job_titles = json.loads(response.context['job_titles'])
        job_applicants = json.loads(response.context['job_applicants'])
        job_interviews = json.loads(response.context['job_interviews'])
        
        self.assertEqual(len(job_titles), 0)
        self.assertEqual(len(job_applicants), 0)
        self.assertEqual(len(job_interviews), 0)
        
        # Analytics should handle zero cases
        self.assertEqual(response.context['total_jobs'], 0)
        self.assertEqual(response.context['total_applicants'], 0)
        self.assertEqual(response.context['average_apps_per_job'], 0)

    