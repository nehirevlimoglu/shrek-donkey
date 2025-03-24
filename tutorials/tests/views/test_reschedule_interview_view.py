import datetime
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta, time
from django.http import Http404
from django.contrib.auth import get_user_model

from tutorials.models.employer_models import Interview, Job, Employer, Candidate

User = get_user_model()

@override_settings(
    TEMPLATES=[{
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': False,
        'OPTIONS': {
            'loaders': [
                (
                    'django.template.loaders.locmem.Loader', {
                        'reschedule_interview.html': 'Dummy reschedule interview template content',
                        'interview_detail.html': 'Dummy interview detail template content',
                    }
                )
            ],
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    }]
)
class RescheduleInterviewViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.today = timezone.now().date()

        # Create a user (for simplicity, using an applicant role for candidate)
        self.user = User.objects.create_user(
            username="candidateuser",
            email="candidate@example.com",
            password="password123",
            role="Applicant"
        )
        self.client.force_login(self.user)

        # Create an Employer instance (needed for Job)
        self.employer = Employer.objects.create(
            user=self.user,
            username="employeruser",
            email="employer@example.com",
            company_name="Test Company",
            company_location="Test City",
            industry="Tech"
        )

        # Create a Job instance.
        self.job = Job.objects.create(
            employer=self.employer,
            title="Test Job",
            description="Job description",
            application_deadline=self.today + timedelta(days=10)
        )

        # Create a Candidate instance.
        self.candidate = Candidate.objects.create(
            user=self.user,
            job=self.job,
            application_status="Pending",
            application_date=timezone.now(),
            first_name="John",
            last_name="Doe"
        )

        # Create an Interview instance.
        self.interview = Interview.objects.create(
            candidate=self.candidate,
            job=self.job,
            date=self.today + timedelta(days=1),
            time=time(10, 0),
            interview_link="http://example.com/interview",
            notes="Original interview notes"
        )

        # Build URL for reschedule_interview view.
        self.url = reverse("reschedule_interview", kwargs={"pk": self.interview.pk})

    def test_get_reschedule_interview_view(self):
        """Test that a GET request returns the reschedule interview form with the interview in context."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        # Check that our dummy template content is present.
        self.assertIn("Dummy reschedule interview template content", response.content.decode())
        self.assertIn("interview", response.context)
        self.assertEqual(response.context["interview"].pk, self.interview.pk)

    def test_post_valid_reschedule_interview(self):
        """Test that a valid POST updates the interview date and time and redirects to interview_detail."""
        # New interview date/time.
        new_date = (self.today + timedelta(days=2)).isoformat()  # ISO format string.
        new_time = "11:30:00"
        data = {
            "date": new_date,
            "time": new_time,
        }
        response = self.client.post(self.url, data)
        # Expect redirect to interview_detail; assuming URL name "interview_detail" with pk parameter.
        expected_redirect = reverse("interview_detail", kwargs={"pk": self.interview.pk})
        self.assertRedirects(response, expected_redirect)
        # Refresh the interview from DB and check updates.
        self.interview.refresh_from_db()
        self.assertEqual(self.interview.date.isoformat(), new_date)
        # Compare time by hour and minute.
        self.assertEqual(self.interview.time.hour, int(new_time.split(":")[0]))
        self.assertEqual(self.interview.time.minute, int(new_time.split(":")[1]))

    def test_interview_not_found(self):
        """Test that an invalid interview pk returns a 404 response."""
        invalid_url = reverse("reschedule_interview", kwargs={"pk": 99999})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, 404)
