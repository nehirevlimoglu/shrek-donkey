from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages

from tutorials.models.employer_models import Candidate, Employer, Job
from tutorials.models.applicants_models import Applicant, ApplicantNotification

User = get_user_model()

class AcceptCandidateViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create a candidate user.
        self.candidate_user = User.objects.create_user(
            username="candidateuser",
            email="candidate@example.com",
            password="password123",
            role="Applicant"
        )
        # Create an Applicant profile for this user.
        self.applicant = Applicant.objects.create(
            user=self.candidate_user,
            # add other required fields as necessary
        )
        # Create an employer (and associated user) for the job.
        self.employer_user = User.objects.create_user(
            username="employeruser",
            email="employer@example.com",
            password="password123",
            role="Employer"
        )
        self.employer = Employer.objects.create(
            user=self.employer_user,
            username="employeruser",  # must match request.user.username when needed
            email="employer@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )
        # Create a Job instance.
        from django.utils import timezone
        self.job = Job.objects.create(
            employer=self.employer,
            title="Software Engineer",
            description="Job description",
            application_deadline=timezone.now().date() + timezone.timedelta(days=10)
        )
        # Create a Candidate instance (application under review initially)
        self.candidate = Candidate.objects.create(
            user=self.candidate_user,
            job=self.job,
            application_status="under_review",
            application_date=timezone.now(),
            first_name="John",
            last_name="Doe"
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
        notification = ApplicantNotification.objects.filter(applicant=self.applicant).first()
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
        self.applicant.delete()
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("message"), "Candidate accepted successfully!")
        self.assertEqual(data.get("status"), "Hired")
        # Verify candidate status updated.
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
