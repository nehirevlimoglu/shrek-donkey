from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from tutorials.models.user_model import User
from tutorials.models.employer_models import Employer, Job, Candidate, Interview
from datetime import date, time, timedelta
from faker import Faker
import random

# ✅ Predefined user fixtures (Employers, Admins, and Applicants)
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
    """Automatically seeds Employers, Admins, and Applicants into the database."""
    
    USER_COUNT = 25
    EMPLOYER_COUNT = 5
    APPLICANT_COUNT = 15
    ADMIN_COUNT = 5
    DEFAULT_PASSWORD = 'Password123'
    help = 'Seeds the database with sample Employers, Admins, and Applicants'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.faker = Faker('en_GB')

    def handle(self, *args, **options):
        """Main function to create all users"""
        self.create_users()
        print("\n✅ Seeding complete. Summary:")
        self.list_all_users()

        self.create_employers_from_users()   # Only needed if Employer extends User
        self.create_jobs()
        self.create_candidates()
        self.create_interviews()

        print("Seeding complete.")

    def create_users(self):
        """Creates users from fixtures and generates random ones"""
        self.generate_user_fixtures()
        self.generate_random_users()

    def generate_user_fixtures(self):
        """Creates predefined users from user_fixtures list"""
        for data in user_fixtures:
            self.try_create_user(data)

    def generate_random_users(self):
        """Creates additional random users to meet the count requirements"""
        user_count = User.objects.count()
        employer_count = Employer.objects.count()
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
        """Generates a new user with Faker"""
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        email = create_email(first_name, last_name)

        # Ensure the email is unique
        while User.objects.filter(email=email).exists():
            first_name = self.faker.first_name()
            last_name = self.faker.last_name()
            email = create_email(first_name, last_name)

        username = create_username(first_name, last_name)

        self.try_create_user({
            'username': username,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'role': role,
        })

    def try_create_user(self, data):
        """Attempts to create a user and handles exceptions"""
        try:
            self.create_user(data)
        except Exception as e:
            print(f"⚠️ Error creating user: {e}")

    def create_user(self, data):
        """Creates a user and links Employers separately"""
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                "email": data['email'],
                "password": make_password(self.DEFAULT_PASSWORD),  # Hash password correctly
                "first_name": data['first_name'],
                "last_name": data['last_name'],
                "role": data['role'],
                "is_active": True  # Ensure active status
            }
        )

    def create_employers_from_users(self):
        fake = Faker()
        employer_users = self.users.filter(role='Employer')
        for user in employer_users:
            if not Employer.objects.filter(pk=user.pk).exists():
                Employer.objects.create(
                    user_ptr_id=user.pk,
                    username=user.username,
                    email=user.email,
                    password=user.password,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    role=user.role,
                    company_name=fake.company(),
                    company_location=fake.city(),
                    industry="Tech",
                    company_size=fake.random_int(min=1, max=500),
                    account_status="Active",
                    subscription_plan="Free",
                    is_verified=True
                )
                print(f"Created Employer for user {user.username}")

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
                    contact_email=employer.email,
                )
                print(f"Created Job '{job.title}' for employer {employer.username}")

    def create_candidates(self):
        jobs = list(Job.objects.all())
        applicants = self.users.filter(role='Applicant')

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

        if created:
            print(f"✅ {data['role']} User created: {user}")

        # ✅ If the user is an Employer, create an Employer instance
        if data['role'] == 'Employer':
            employer, emp_created = Employer.objects.get_or_create(
                username=user.username,  # Store the username separately
                defaults={
                    "email": user.email,
                    "company_name": f"{user.first_name} {user.last_name} Corp",
                    "company_location": "Unknown",
                    "industry": "General",
                    "is_verified": True
                }
            )
            if emp_created:
                print(f"✅ Employer profile created for {user.username}")

    def list_all_users(self):
        """Displays a summary of all created users"""
        print("\n🔹 **Employers:**")
        for employer in Employer.objects.all():
            print(f"  ✅ {employer.username} | {employer.company_name}")

        print("\n🔹 **Admins:**")
        for admin in User.objects.filter(role="Admin"):
            print(f"  ✅ {admin.username} | {admin.email}")

        print("\n🔹 **Applicants:**")
        for applicant in User.objects.filter(role="Applicant"):
            print(f"  ✅ {applicant.username} | {applicant.email}")

def create_username(first_name, last_name):
    return '@' + first_name.lower() + last_name.lower()

def create_email(first_name, last_name):
    return first_name.lower() + '@example.org'



