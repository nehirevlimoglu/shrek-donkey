from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.contrib.auth import get_user_model
from tutorials.models.employer_models import Employer, Job, Candidate, Interview
from datetime import date, time, timedelta
from faker import Faker
import random

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
    help = 'Seeds the database with sample Employers, Admins, and Applicants'

    USER_COUNT = 25
    EMPLOYER_COUNT = 5
    APPLICANT_COUNT = 15
    ADMIN_COUNT = 5
    DEFAULT_PASSWORD = 'Password123'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.faker = Faker('en_GB')

    def handle(self, *args, **options):
        self.create_users()  # from fixtures + random
        print("\n✅ Seeding complete. Summary:")
        self.list_all_users()

        self.create_jobs()
        self.create_candidates()
        self.create_interviews()

        print("Seeding complete.")

    # ---------------------------
    # Create users
    # ---------------------------
    def create_users(self):
        """Creates users from fixtures, then random ones."""
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
        email = create_email(first_name, last_name)

        while User.objects.filter(email=email).exists():
            first_name = self.faker.first_name()
            last_name = self.faker.last_name()
            email = create_email(first_name, last_name)

        username = create_username(first_name, last_name)
        data = {
            'username': username,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'role': role,
        }
        self.try_create_user(data)

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
                "is_active": True
            }
        )
        if created:
            print(f"Created User: {user.username} (role={user.role})")

        if user.role == 'Employer':
            self.create_employer_profile(user)

    def create_employer_profile(self, user):
    # Check if an Employer record already exists for this user
        if not Employer.objects.filter(user=user).exists():
            Employer.objects.create(
                user=user,
                username=user.username,  # Use the unique username from the User
                email=user.email,        # Use the user's email
                company_name=f"{user.first_name} {user.last_name} Corp",
                company_location=self.faker.city(),
                industry="Tech",
                company_size=random.randint(1, 500),
                account_status="Active",
                subscription_plan="Free",
                is_verified=True
            )
            print(f"Created Employer profile for {user.username}")
    # ---------------------------
    # Create Jobs, Candidates, Interviews
    # ---------------------------
    def create_jobs(self):
        fake = Faker()
        for employer in Employer.objects.all():
            for i in range(3):
                title = fake.job()
                job = Job.objects.create(
                    employer=employer,
                    title=title,
                    company_name=employer.company_name,
                    location=fake.city(),
                    job_type="Full Time",
                    salary=fake.random_int(min=30000, max=150000),
                    description=f"Job description for {title}",
                    requirements="Sample requirements",
                    benefits="Some benefits",
                    contact_email=employer.user.email,  # Use the linked User's email
                )
                print(f"Created Job '{job.title}' for employer {employer.user.username}")

    def create_candidates(self):
        jobs = list(Job.objects.all())
        applicants = User.objects.filter(role='Applicant')
        for user in applicants:
            if not jobs:
                break
            job = random.choice(jobs)
            candidate = Candidate.objects.create(
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
            print(f"  ✅ {employer.user.username} | {employer.company_name}")

        print("\n🔹 **Admins:**")
        for admin in User.objects.filter(role="Admin"):
            print(f"  ✅ {admin.username} | {admin.email}")

        print("\n🔹 **Applicants:**")
        for applicant in User.objects.filter(role="Applicant"):
            print(f"  ✅ {applicant.username} | {applicant.email}")

def create_username(first_name, last_name):
    return '@' + first_name.lower() + last_name.lower()

def create_email(first_name, last_name):
    return f"{first_name.lower()}@example.org"