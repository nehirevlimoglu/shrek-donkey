from django.utils import timezone
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.utils import timezone
from tutorials.models.employer_models import Employer, Job, Candidate
from tutorials.models.applicants_models import Applicant, ApplicantNotification, Application

User = get_user_model()

class AcceptCandidateViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an employer user who will be logged in.
        self.employer_user = User.objects.create_user(
            username="employeruser",
            email="employer@example.com",
            password="password123",
            role="Employer"
        )
        self.client.force_login(self.employer_user)
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username="employeruser",
            email="employer@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )
        
        # Create a separate applicant user.
        self.applicant_user = User.objects.create_user(
            username="applicantuser",
            email="applicant@example.com",
            password="password123",
            role="Applicant"
        )
        # Create an Applicant profile for the applicant user.
        self.applicant_obj = Applicant.objects.create(
            user=self.applicant_user,
            # Additional fields as needed.
        )
        
        # Create a Job instance (posted by the employer).
        self.job = Job.objects.create(
            employer=self.employer,
            title="Software Engineer",
            description="Job description",
            application_deadline=timezone.now().date() + timezone.timedelta(days=10)
        )
        
        # Create a Candidate instance for the applicant.
        self.candidate = Candidate.objects.create(
            user=self.applicant_user,
            job=self.job,
            application_status="under_review",
            application_date=timezone.now(),
            first_name="John",
            last_name="Doe"
        )
        
        # **Create an Application instance** for this candidate.
        self.application = Application.objects.create(
            applicant=self.applicant_obj,
            job=self.job,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            phone="1234567890",
            address="123 Main St",
            education=[],            # dummy data
            work_experience=[],      # dummy data
            current_job_title="Developer",
            current_employer="Some Company",
            linkedin_profile="",
            portfolio_website="",
            how_did_you_hear="other",
            sponsorship_needed="no",
            confirm_information=True,
            status="under_review"
        )
        
        # Build URL for the view.
        self.url = reverse("accept_candidate", kwargs={"candidate_id": self.candidate.id})


    def test_accept_candidate_success(self):
        """Test that a valid POST updates candidate status to 'Hired' and creates a notification."""
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("message"), "Candidate accepted successfully!")
        self.assertEqual(data.get("status"), "Hired")
        # Refresh candidate from DB.
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.application_status, "Hired")
        # Verify that an ApplicantNotification was created.
        notification = ApplicantNotification.objects.filter(applicant=self.applicant_obj).first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.title, "Congratulations, You're Hired!")
        expected_message = (
            f"You have been hired for the {self.job.title} position. "
            f"Please contact {self.employer.email} for further details."
        )
        self.assertEqual(notification.message, expected_message)


    def test_accept_candidate_already_hired(self):
        """Test that if the candidate is already 'Hired', a POST returns a 400 error."""
        self.candidate.application_status = "Hired"
        self.candidate.save()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data.get("error"), "Status cannot be changed once set.")

    def test_accept_candidate_already_rejected(self):
        """Test that if the candidate is already 'Rejected', a POST returns a 400 error."""
        self.candidate.application_status = "Rejected"
        self.candidate.save()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data.get("error"), "Status cannot be changed once set.")

    def test_accept_candidate_no_applicant_profile(self):
        """Test that if the Applicant profile does not exist, the candidate is still accepted but no notification is created."""
        # Delete the Applicant profile.
        self.applicant_obj.delete()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("message"), "Candidate accepted successfully!")
        self.assertEqual(data.get("status"), "Hired")
        # Refresh candidate from DB.
        self.candidate.refresh_from_db()
        self.assertEqual(self.candidate.application_status, "Hired")
        # There should be no notification for this applicant.
        notifications = ApplicantNotification.objects.filter(applicant__user=self.candidate.user)
        self.assertEqual(notifications.count(), 0)

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.post(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)
