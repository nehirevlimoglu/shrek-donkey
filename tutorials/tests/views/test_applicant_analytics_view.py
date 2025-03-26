from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from tutorials.models.applicants_models import Applicant, Application
from tutorials.models.employer_models import Job, Employer, JobTitle, Interview, Candidate
from datetime import timedelta

User = get_user_model()

class ApplicantAnalyticsTests(TestCase):
    """Test suite for applicant analytics functionality"""

    def setUp(self):
        self.applicant_user = User.objects.create_user(
            username='@testapplicant',
            password='testpass123',
            email='applicant@test.com',
            first_name='Test',
            last_name='Applicant',
            role='Applicant'
        )

        self.employer_user = User.objects.create_user(
            username='@testemployer',
            password='testpass123',
            email='employer@test.com',
            role='Employer'
        )

        self.employer = Employer.objects.create(
            user=self.employer_user,
            company_name='Test Company'
        )

        self.applicant = Applicant.objects.create(
            user=self.applicant_user,
            degree='Computer Science',
            salary_preferences='80000-100000',
            location_preferences='Remote'
        )

        # Use get_or_create to avoid unique constraint issues
        self.job_title, created = JobTitle.objects.get_or_create(title="Software Engineer")

        self.jobs = []
        for i in range(5):
            job = Job.objects.create(
                employer=self.employer,
                title=f"Test Job {i}",
                description=f"Test Description {i}",
                salary=80000 + (i * 10000),
                location="Remote",
                job_type="Full-time",
                status="approved"
            )
            self.jobs.append(job)

        self.create_test_applications()

        candidate = Candidate.objects.create(
            user=self.applicant_user,
            job=self.jobs[1],
            application_status="Interview",
            first_name="Test",
            last_name="Applicant"
        )

        Interview.objects.create(
            candidate=candidate,
            job=self.jobs[1],
            date=timezone.now().date() + timedelta(days=1),
            time=timezone.now().time()
        )

        self.client = Client()
        self.client.login(username='@testapplicant', password='testpass123')


    def create_test_applications(self):
        statuses = ['pending', 'interviewed', 'hired', 'rejected']
        self.applications = []

        for i, job in enumerate(self.jobs):
            status = statuses[i % len(statuses)]
            application = Application.objects.create(
                applicant=self.applicant,
                job=job,
                status=status,
                applied_at=timezone.now() - timedelta(days=i*7),
                confirm_information=True if status == 'hired' else False
            )
            self.applications.append(application)

    def test_view_analytics_authenticated(self):
        response = self.client.get(reverse('applicants-analytics'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'applicants_analytics.html')

        self.assertIn('total_applications', response.context)
        self.assertIn('interviews_scheduled', response.context)
        self.assertIn('job_offers_received', response.context)
        self.assertIn('offer_acceptance_rate', response.context)
        self.assertIn('offer_chart_data', response.context)

        self.assertEqual(response.context['total_applications'], 5)
        self.assertEqual(response.context['interviews_scheduled'], 1)
        self.assertEqual(response.context['job_offers_received'], 1)

        self.assertTrue(isinstance(response.context['offer_chart_data'], list))

    def test_view_analytics_unauthenticated(self):
        self.client.logout()
        response = self.client.get(reverse('applicants-analytics'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, f"{reverse('log_in')}?next={reverse('applicants-analytics')}")

    def test_non_applicant_access(self):
        self.client.login(username='@testemployer', password='testpass123')
        response = self.client.get(reverse('applicants-analytics'))
        self.assertEqual(response.status_code, 403)

    def test_empty_analytics(self):
        Application.objects.all().delete()
        response = self.client.get(reverse('applicants-analytics'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_applications'], 0)
        self.assertEqual(response.context['interviews_scheduled'], 0)
        self.assertEqual(response.context['job_offers_received'], 0)
        self.assertEqual(response.context['offer_acceptance_rate'], 0)
        self.assertEqual(response.context['offer_chart_data'], [0, 0])

    def test_offer_acceptance_breakdown(self):
        response = self.client.get(reverse('applicants-analytics'))
        breakdown = response.context['offer_chart_data']
        self.assertTrue(isinstance(breakdown, list))
        self.assertEqual(len(breakdown), 2)
        self.assertTrue(all(isinstance(count, int) for count in breakdown))

    def test_offer_acceptance_rate(self):
        for i in range(2):
            job = Job.objects.create(
                employer=self.employer,
                title=f"Extra Job {i}",
                description=f"Description {i}",
                salary=90000,
                location="Remote",
                job_type="Full-time",
                status="approved"
            )
            Application.objects.create(
                applicant=self.applicant,
                job=job,
                status="hired",
                applied_at=timezone.now(),
                confirm_information=bool(i)
            )

        response = self.client.get(reverse('applicants-analytics'))
        self.assertEqual(response.context['job_offers_received'], 3)
        self.assertEqual(response.context['offer_acceptance_rate'], 75.0)


    def test_applications_list(self):
        response = self.client.get(reverse('applicants-analytics'))

        self.assertIn('applications', response.context)
        applications = response.context['applications']

        self.assertEqual(applications.count(), Application.objects.filter(applicant=self.applicant).count())
        self.assertTrue(all(app.job in self.jobs for app in applications))