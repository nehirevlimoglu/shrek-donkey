from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.timezone import now, timedelta
from tutorials.models.employer_models import Employer, Job, Candidate
from tutorials.models.applicants_models import Applicant, Application
from django.contrib import messages
from django.contrib.messages import get_messages

User = get_user_model()

class EmployerCandidatesTests(TestCase):
    """Test suite for employer candidates functionality"""

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

        # Create jobs
        self.job1 = Job.objects.create(
            employer=self.employer,
            title="Software Engineer",
            description="Job 1 description",
            location="Test Location",
            job_type="Full Time",
            salary="100000",
            application_deadline=now().date() + timedelta(days=30)
        )

        self.job2 = Job.objects.create(
            employer=self.employer,
            title="Data Scientist",
            description="Job 2 description",
            location="Remote",
            job_type="Full Time",
            salary="120000",
            application_deadline=now().date() + timedelta(days=30)
        )

        # Create applicant users and candidates with different degrees and statuses
        self.create_test_candidates()

        self.client = Client()
        self.client.force_login(self.employer_user)

    def create_test_candidates(self):
        """Helper method to create test candidates with different attributes"""
        # Candidate 1 - Software Engineer position
        user1 = User.objects.create_user(
            username="candidate1",
            password="pass123",
            email="candidate1@example.com",
            role='Applicant'
        )
        self.candidate1 = Candidate.objects.create(
            user=user1,
            job=self.job1,
            first_name="John",
            last_name="Doe",
            application_date=now(),
            degree="Computer Science",
            application_status="Pending"
        )

        # Candidate 2 - Software Engineer position
        user2 = User.objects.create_user(
            username="candidate2",
            password="pass123",
            email="candidate2@example.com",
            role='Applicant'
        )
        self.candidate2 = Candidate.objects.create(
            user=user2,
            job=self.job1,
            first_name="Jane",
            last_name="Smith",
            application_date=now(),
            degree="Information Technology",
            application_status="Interview"
        )

        # Candidate 3 - Data Scientist position
        user3 = User.objects.create_user(
            username="candidate3",
            password="pass123",
            email="candidate3@example.com",
            role='Applicant'
        )
        self.candidate3 = Candidate.objects.create(
            user=user3,
            job=self.job2,
            first_name="Bob",
            last_name="Wilson",
            application_date=now(),
            degree="Data Science",
            application_status="Hired"
        )

    def test_employer_candidates_view(self):
        """Test basic candidates view without filters"""
        response = self.client.get(reverse('employer_candidates'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'employer_candidates.html')
        
        # Check context data
        self.assertIn('candidates', response.context)
        self.assertIn('jobs', response.context)
        self.assertIn('statuses', response.context)
        self.assertIn('degrees', response.context)
        
        # Verify all candidates are present
        candidates = response.context['candidates']
        self.assertEqual(candidates.count(), 3)

    def test_employer_candidates_job_filter(self):
        """Test filtering candidates by job"""
        response = self.client.get(f"{reverse('employer_candidates')}?job={self.job1.id}")
        
        candidates = response.context['candidates']
        self.assertEqual(candidates.count(), 2)
        self.assertTrue(all(c.job.id == self.job1.id for c in candidates))

    def test_employer_candidates_status_filter(self):
        """Test filtering candidates by status"""
        response = self.client.get(f"{reverse('employer_candidates')}?status=Hired")
        
        candidates = response.context['candidates']
        self.assertEqual(candidates.count(), 1)
        self.assertEqual(candidates[0].application_status, "Hired")

    def test_employer_candidates_degree_filter(self):
        """Test filtering candidates by degree"""
        response = self.client.get(f"{reverse('employer_candidates')}?degree=Computer Science")
        
        candidates = response.context['candidates']
        self.assertEqual(candidates.count(), 1)
        self.assertEqual(candidates[0].degree, "Computer Science")

    def test_employer_candidates_multiple_filters(self):
        """Test applying multiple filters"""
        url = (f"{reverse('employer_candidates')}?"
               f"job={self.job1.id}&status=Interview&degree=Information Technology")
        response = self.client.get(url)
        
        candidates = response.context['candidates']
        self.assertEqual(candidates.count(), 1)
        self.assertEqual(candidates[0].first_name, "Jane")

    def test_employer_candidates_unauthorized(self):
        """Test access by non-employer user"""
        # Create and login as non-employer user
        regular_user = User.objects.create_user(
            username="regular_user",
            password="pass123",
            email="regular@example.com",
            role='Applicant'
        )
        self.client.force_login(regular_user)
        
        response = self.client.get(reverse('employer_candidates'))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content.decode(), "You are not authorized to view this page.")

    def test_employer_candidates_no_employer_profile(self):
        """Test access by user without employer profile"""
        # Create employer user without profile
        user_without_profile = User.objects.create_user(
            username="no_profile",
            password="pass123",
            email="no_profile@example.com",
            role='Employer'
        )
        self.client.force_login(user_without_profile)
        
        response = self.client.get(reverse('employer_candidates'))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.content.decode(), "You are not authorized to view this page.")

    def test_applicant_profile_view(self):
        """Test viewing applicant profile"""
        # First create an Applicant instance for the candidate's user
        applicant = Applicant.objects.create(
            user=self.candidate1.user,
            degree='Computer Science',
            salary_preferences='50000-70000',
            location_preferences='Remote'
        )
        
        # Create an Application instance
        application = Application.objects.create(
            applicant=applicant,
            job=self.job1,
            status='pending'
        )
        
        response = self.client.get(reverse('applicant_profile', args=[self.candidate1.id]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'applicant_profile.html')
        self.assertEqual(response.context['candidate'], self.candidate1)
        self.assertEqual(response.context['application'], application)

    def test_applicant_profile_nonexistent(self):
        """Test viewing profile of non-existent applicant"""
        response = self.client.get(reverse('applicant_profile', args=[99999]))
        
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.content.decode(), "Candidate does not exist.")

    def test_applicant_profile_update_status(self):
        """Test updating applicant status via POST"""
        # Create necessary Applicant and Application instances
        applicant = Applicant.objects.create(
            user=self.candidate1.user,
            degree='Computer Science',
            salary_preferences='50000-70000',
            location_preferences='Remote'
        )
        
        application = Application.objects.create(
            applicant=applicant,
            job=self.job1,
            status='pending'
        )
        
        response = self.client.post(
            reverse('applicant_profile', args=[self.candidate1.id]),
            {'status': 'Interview'}
        )
        
        # Check redirect
        self.assertRedirects(response, reverse('applicant_profile', args=[self.candidate1.id]))
        
        # Verify status was updated
        self.candidate1.refresh_from_db()
        self.assertEqual(self.candidate1.application_status, "Interview")
        
        # Check success message
        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(str(messages[0]), "Application status updated successfully!")

    def test_accept_candidate(self):
        """Test accepting a candidate"""
        response = self.client.post(reverse('accept_candidate', args=[self.candidate1.id]))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], "Hired")
        self.assertEqual(data['message'], "Candidate accepted successfully!")
        
        # Verify database update
        self.candidate1.refresh_from_db()
        self.assertEqual(self.candidate1.application_status, "Hired")

    def test_reject_candidate(self):
        """Test rejecting a candidate"""
        response = self.client.post(reverse('reject_candidate', args=[self.candidate1.id]))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], "Rejected")
        self.assertEqual(data['message'], "Candidate rejected successfully!")
        
        # Verify database update
        self.candidate1.refresh_from_db()
        self.assertEqual(self.candidate1.application_status, "Rejected")

    def test_accept_already_hired_candidate(self):
        """Test attempting to accept an already hired candidate"""
        # First hire the candidate
        self.candidate1.application_status = "Hired"
        self.candidate1.save()
        
        response = self.client.post(reverse('accept_candidate', args=[self.candidate1.id]))
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['error'], "Status cannot be changed once set.")

    def test_reject_already_rejected_candidate(self):
        """Test attempting to reject an already rejected candidate"""
        # First reject the candidate
        self.candidate1.application_status = "Rejected"
        self.candidate1.save()
        
        response = self.client.post(reverse('reject_candidate', args=[self.candidate1.id]))
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['error'], "Status cannot be changed once set.")

    def test_accept_nonexistent_candidate(self):
        """Test accepting a non-existent candidate"""
        response = self.client.post(reverse('accept_candidate', args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_reject_nonexistent_candidate(self):
        """Test rejecting a non-existent candidate"""
        response = self.client.post(reverse('reject_candidate', args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_invalid_status_update(self):
        """Test updating applicant status with invalid status"""
        # Create necessary Applicant and Application instances
        applicant = Applicant.objects.create(
            user=self.candidate1.user,
            degree='Computer Science',
            salary_preferences='50000-70000',
            location_preferences='Remote'
        )
        
        application = Application.objects.create(
            applicant=applicant,
            job=self.job1,
            status='pending'
        )
        
        response = self.client.post(
            reverse('applicant_profile', args=[self.candidate1.id]),
            {'status': 'InvalidStatus'}
        )
        
        # Should redirect without updating status
        self.assertRedirects(response, reverse('applicant_profile', args=[self.candidate1.id]))
        
        # Verify status was not changed
        self.candidate1.refresh_from_db()
        self.assertEqual(self.candidate1.application_status, "Pending") 