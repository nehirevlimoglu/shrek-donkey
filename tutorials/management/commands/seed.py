from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from datetime import date, time, timedelta
from faker import Faker
import random

from tutorials.models.user_model import User
from tutorials.models.employer_models import Employer, Job, Candidate, Interview, JobTitle
from tutorials.models.applicants_models import Applicant
from tutorials.models.admin_models import Admin

User = get_user_model()

user_fixtures = [
    {'username': '@damla', 'email': 'damla@example.org', 'first_name': 'Damla', 'last_name': 'Sen', 'role': 'Employer'},
    {'username': '@tan', 'email': 'tan@example.org', 'first_name': 'Tan', 'last_name': 'Yukseloglu', 'role': 'Employer'},
    {'username': '@rares', 'email': 'rares@example.org', 'first_name': 'Rares', 'last_name': 'Filimon', 'role': 'Applicant'},
    {'username': '@mert', 'email': 'mert@example.org', 'first_name': 'Mert', 'last_name': 'Johnson', 'role': 'Employer'},
    {'username': '@jj', 'email': 'jj@example.org', 'first_name': 'JJ', 'last_name': 'Zhou', 'role': 'Admin'},
    {'username': '@finn', 'email': 'finn@example.org', 'first_name': 'Finn', 'last_name': 'Corney', 'role': 'Employer'},
    {'username': '@liam', 'email': 'liam@example.org', 'first_name': 'Liam', 'last_name': 'Ferran', 'role': 'Applicant'},
    {'username': '@trong', 'email': 'trong@example.org', 'first_name': 'Trong', 'last_name': 'Vu', 'role': 'Admin'},
    {'username': '@nehir', 'email': 'nehir@example.org', 'first_name': 'Nehir', 'last_name': 'Evlimoglu', 'role': 'Employer'},
]

class Command(BaseCommand):
    USER_COUNT = 25
    EMPLOYER_COUNT = 5
    APPLICANT_COUNT = 15
    ADMIN_COUNT = 5
    DEFAULT_PASSWORD = 'Password123'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.faker = Faker('en_GB')

    def handle(self, *args, **options):
        self.create_users()
        self.create_jobs()
        self.create_candidates()
        self.create_interviews()
        # You can add more methods here later like:
        # self.create_applications()
        # self.create_notifications()
        # self.create_admin_preferences()
        # self.create_applicant_notifications()
        # self.create_employer_notifications()
        # self.create_employer_events()
        self.list_all_users()
        print("\n✅ Seeding complete.")

    def create_users(self):
        self.generate_user_fixtures()
        self.generate_random_users()

    def generate_user_fixtures(self):
        for data in user_fixtures:
            self.try_create_user(data)

    def generate_random_users(self):
        user_count = User.objects.count()
        employer_count = User.objects.filter(role='Employer').count()
        applicant_count = User.objects.filter(role='Applicant').count()
        admin_count = User.objects.filter(role='Admin').count()

        while user_count < self.USER_COUNT:
            print(f"Seeding user {user_count + 1}/{self.USER_COUNT}", end='\r')
            if employer_count < self.EMPLOYER_COUNT:
                self.generate_user('Employer')
                employer_count += 1
            elif admin_count < self.ADMIN_COUNT:
                self.generate_user('Admin')
                admin_count += 1
            else:
                self.generate_user('Applicant')
                applicant_count += 1
            user_count = User.objects.count()
        print("✅ Additional user seeding complete.")

    def generate_user(self, role):
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        email = self.create_email(first_name, last_name)

        while User.objects.filter(email=email).exists():
            first_name = self.faker.first_name()
            last_name = self.faker.last_name()
            email = self.create_email(first_name, last_name)

        username = self.create_username(first_name, last_name)

        self.try_create_user({
            'username': username,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'role': role,
        })

    def try_create_user(self, data):
        try:
            self.create_user(data)
        except Exception as e:
            print(f"⚠️ Error creating user: {e}")

    def create_user(self, data):
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                "email": data['email'],
                "password": make_password(self.DEFAULT_PASSWORD),
                "first_name": data['first_name'],
                "last_name": data['last_name'],
                "role": data['role'],
                "is_active": True,
                "is_staff": data['role'] == "Admin",
                "is_superuser": data['role'] == "Admin"
            }
        )
        if created:
            print(f"Created User: {user.username} (role={user.role})")

        if user.role == 'Employer':
            self.create_employer_profile(user)
        elif user.role == 'Applicant':
            self.create_applicant_profile(user)
        elif user.role == 'Admin':
            self.create_admin_profile(user)

    def create_employer_profile(self, user):
        if not Employer.objects.filter(user=user).exists():
            Employer.objects.create(
                user=user,
                username=user.username,
                email=user.email,
                company_name=f"{user.first_name} {user.last_name} Corp",
                company_website=self.faker.url(),
                company_location=self.faker.city(),
                industry="Tech",
                company_size=random.randint(1, 500),
                account_status="Active",
                subscription_plan="Free",
                is_verified=True
            )
            print(f"Created Employer profile for {user.username}")

    def create_applicant_profile(self, user):
        if not Applicant.objects.filter(user=user).exists():
            applicant = Applicant.objects.create(
                user=user,
                degree="Computer Science",
                salary_preferences="$50,000-$70,000",
                location_preferences="Remote",
                cv="uploads/cv/dummy_cv.pdf"
            )
            job_titles = JobTitle.objects.filter(title__icontains="Software")[:3]
            applicant.job_preferences.set(job_titles)
            print(f"Created Applicant profile for {user.username}")

    def create_admin_profile(self, user):
        if not Admin.objects.filter(user=user).exists():
            Admin.objects.create(
                user=user,
                username=user.username,
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                phone_number=self.faker.phone_number()
            )
            print(f"Created Admin profile for {user.username}")

    def create_jobs(self):
        for employer in Employer.objects.all():
            for _ in range(3):
                title = self.faker.job()
                is_approved = random.choice([True, False])  # ✅ Randomly approve some jobs
                job = Job.objects.create(
                    employer=employer,
                    title=title,
                    company_name=employer.company_name,
                    location=self.faker.city(),
                    job_type="Full Time",
                    salary=self.faker.random_int(min=30000, max=150000),
                    description=f"Job description for {title}",
                    requirements="Sample requirements",
                    benefits="Some benefits",
                    contact_email=employer.user.email,
                    status="approved" if is_approved else "pending",  # ✅ Randomized status
                )
                print(f"Created Job '{job.title}' for {employer.user.username} (Status: {job.status})")

    def create_candidates(self):
        jobs = list(Job.objects.all())
        applicants = User.objects.filter(role='Applicant')
        for user in applicants:
            if not jobs:
                break
            job = random.choice(jobs)
            Candidate.objects.create(
                user=user,
                job=job,
                resume=None,
                cover_letter="Looking forward to joining your company!",
            )
            print(f"Created Candidate for user {user.username} on job {job.title}")

    def create_interviews(self):
        interview_date = date.today() + timedelta(days=1)
        interview_time = time(10, 0)
        for cand in Candidate.objects.all():
            Interview.objects.create(
                candidate=cand,
                job=cand.job,
                date=interview_date,
                time=interview_time,
                interview_link="https://zoom.us/fake-interview",
                notes="Initial screening"
            )
            print(f"Created Interview for {cand.user.username} - {cand.job.title}")

    def list_all_users(self):
        print("\n🔹 **Employers (OneToOne)**:")
        for employer in Employer.objects.all():
            print(f"  ✅ {employer.user.username} | {employer.company_name} | Website: {employer.company_website}")

        print("\n🔹 **Admins:**")
        for admin in User.objects.filter(role="Admin"):
            print(f"  ✅ {admin.username} | {admin.email}")
            try:
                admin_profile = Admin.objects.get(user=admin)
                print(f"     Phone: {admin_profile.phone_number}")
            except Admin.DoesNotExist:
                print("     ❌ No admin profile found")

        print("\n🔹 **Applicants:**")
        for applicant in User.objects.filter(role="Applicant"):
            print(f"  ✅ {applicant.username} | {applicant.email}")
            try:
                profile = Applicant.objects.get(user=applicant)
                print(f"     Degree: {profile.degree}")
                print(f"     CV: {profile.cv}")
            except Applicant.DoesNotExist:
                print("     ❌ No applicant profile found")

    @staticmethod
    def create_username(first_name, last_name):
        return f"@{first_name.lower()}{last_name.lower()}"

    @staticmethod
    def create_email(first_name, last_name):
        return f"{first_name.lower()}.{last_name.lower()}@example.com"