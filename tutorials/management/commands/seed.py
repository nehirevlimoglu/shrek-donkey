from django.core.management.base import BaseCommand
from tutorials.models.user_model import User
from tutorials.models.employer_models import Employer, Job, Candidate, Interview
from datetime import date, time, timedelta
from faker import Faker
import random

user_fixtures = [
    {'username': '@damla', 'email': 'Damla@example.org', 'first_name': 'Damla', 'last_name': 'Sen', 'role': 'Employer'},
    {'username': '@tan', 'email': 'Tan@example.org', 'first_name': 'Tan', 'last_name': 'Yukseloglu', 'role': 'Employer'},
    {'username': '@rares', 'email': 'Rares@example.org', 'first_name': 'Rares', 'last_name': 'Filimon', 'role': 'Applicant'},
    {'username': '@mert', 'email': 'Mert@example.org', 'first_name': 'Mert', 'last_name': 'Johnson', 'role': 'Employer'},
    {'username': '@jj', 'email': 'Jj@example.org', 'first_name': 'JJ', 'last_name': 'Zhou', 'role': 'Admin'},
    {'username': '@finn', 'email': 'Finn@example.org', 'first_name': 'Finn', 'last_name': 'Corney', 'role': 'Employer'},
    {'username': '@liam', 'email': 'Liam@example.org', 'first_name': 'Liam', 'last_name': 'Ferran', 'role': 'Applicant'},
    {'username': '@trong', 'email': 'Trong@example.org', 'first_name': 'Trong', 'last_name': 'Vu', 'role': 'Admin'},
    {'username': '@nehir', 'email': 'Nehir@example.org', 'first_name': 'Nehir', 'last_name': 'Evlimoglu', 'role': 'Employer'},
]

class Command(BaseCommand):
    """Build automation command to seed the database."""

    USER_COUNT = 25
    EMPLOYER_COUNT = 5
    APPLICANT_COUNT = 15
    ADMIN_COUNT = 5
    DEFAULT_PASSWORD = 'Password123'
    help = 'Seeds the database with sample data'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.faker = Faker('en_GB')

    def handle(self, *args, **options):
        self.create_users()
        self.users = User.objects.all()
        print("\nFirst names of all users:")
        for user in User.objects.all():
            print(user.first_name)

        self.create_employers_from_users()   # Only needed if Employer extends User
        self.create_jobs()
        self.create_candidates()
        self.create_interviews()

        print("Seeding complete.")

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

        print("User seeding complete.")

    def generate_user(self, newRole):
        first_name = self.faker.first_name()
        last_name = self.faker.last_name()
        email = create_email(first_name, last_name)

        # Ensure the email is unique
        while User.objects.filter(email=email).exists():
            first_name = self.faker.first_name()
            last_name = self.faker.last_name()
            email = create_email(first_name, last_name)

        username = create_username(first_name, last_name)
        role = newRole

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
            print(f"Error creating user: {e}")

    def create_user(self, data):
        User.objects.create_user(
            username=data['username'],
            email=data['email'],
            password=self.DEFAULT_PASSWORD,
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data['role']
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


def create_username(first_name, last_name):
    return '@' + first_name.lower() + last_name.lower()

def create_email(first_name, last_name):
    return first_name.lower() + '@example.org'



