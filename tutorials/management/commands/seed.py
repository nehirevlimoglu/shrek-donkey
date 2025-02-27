from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from tutorials.models.user_model import User
from tutorials.models.employer_models import Employer
from tutorials.models.applicants_models import Applicant, FavoriteJob
from faker import Faker
from tutorials.models.employer_models import Job, Employer
from django.utils import timezone
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

# Simplified job fixtures
job_fixtures = [
    {
        "title": "Software Engineer",
        "description": "Entry level software engineer position",
        "requirements": "Python, JavaScript",
        "salary": 120000.00,
        "job_type": "Full Time"
    },
    {
        "title": "Data Analyst",
        "description": "Junior data analyst role",
        "requirements": "SQL, Excel",
        "salary": 85000.00,
        "job_type": "Full Time"
    },
    {
        "title": "Marketing Intern",
        "description": "Marketing internship opportunity",
        "requirements": "Social media experience",
        "salary": 45000.00,
        "job_type": "Part Time"
    }
]

class Command(BaseCommand):
    """Automatically seeds Employers, Admins, and Applicants into the database."""
    
    USER_COUNT = 25
    EMPLOYER_COUNT = 5
    APPLICANT_COUNT = 15
    ADMIN_COUNT = 5
    DEFAULT_PASSWORD = 'Password123'
    JOB_COUNT = 15  # Total number of jobs to create
    help = 'Seeds the database with sample Employers, Admins, and Applicants'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.faker = Faker('en_GB')

    def handle(self, *args, **options):
        """Main function to create all users and jobs"""
        self.create_users()
        self.create_jobs()
        self.create_favorite_jobs()
        print("\n✅ Seeding complete. Summary:")
        self.list_all_users()
        self.list_all_jobs()

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
        """Creates a user and links Employers/Applicants separately"""
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
            print(f"✅ {data['role']} User created: {user}")

            # Create Employer profile
            if data['role'] == 'Employer':
                employer, emp_created = Employer.objects.get_or_create(
                    username=user.username,
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
            
            # Create Applicant profile
            elif data['role'] == 'Applicant':
                applicant, app_created = Applicant.objects.get_or_create(
                    user=user,
                    defaults={
                        "degree": "Computer Science",
                        "salary_preferences": "$50,000-$70,000",
                        "job_preferences": "Software Development",
                        "location_preferences": "Remote"
                    }
                )
                if app_created:
                    print(f"✅ Applicant profile created for {user.username}")

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
            # Also print the associated Applicant profile
            try:
                profile = Applicant.objects.get(user=applicant)
                print(f"     Degree: {profile.degree}")
            except Applicant.DoesNotExist:
                print("     ❌ No applicant profile found")

    def create_jobs(self):
        """Creates jobs from fixtures and generates random ones"""
        print("\nCreating job listings...")
        
        # Create jobs from fixtures first
        for job_data in job_fixtures:
            # Get a random employer
            employer = Employer.objects.order_by('?').first()
            if employer:
                self.create_job(job_data, employer)

        # Generate additional random jobs to meet JOB_COUNT
        job_count = Job.objects.count()
        while job_count < self.JOB_COUNT:
            print(f"Seeding job {job_count + 1}/{self.JOB_COUNT}", end='\r')
            employer = Employer.objects.order_by('?').first()
            if employer:
                self.generate_random_job(employer)
            job_count = Job.objects.count()

        print("✅ Job seeding complete.")

    def create_job(self, data, employer):
        """Creates a single job listing with minimal required fields"""
        job, created = Job.objects.get_or_create(
            title=data['title'],
            employer=employer,
            defaults={
                'description': data['description'],
                'requirements': data['requirements'],
                'salary': data['salary'],
                'job_type': data['job_type'],
                'created_at': timezone.now()
            }
        )
        if created:
            print(f"✅ Job created: {job.title}")

    def generate_random_job(self, employer):
        """Generates a random job listing"""
        job_titles = ["Software Developer", "Product Manager", "UX Designer", 
                     "Data Scientist", "DevOps Engineer", "QA Engineer"]
        locations = ["London, UK", "New York, NY", "San Francisco, CA", 
                    "Toronto, CA", "Berlin, DE", "Sydney, AU"]
        job_types = ["Full-Time", "Part-Time", "Contract", "Remote"]
        salary_ranges = ["$70,000-$90,000", "$90,000-$120,000", 
                        "$120,000-$150,000", "$150,000+"]

        data = {
            'title': self.faker.choice(job_titles),
            'location': self.faker.choice(locations),
            'salary': self.faker.choice(salary_ranges),
            'job_type': self.faker.choice(job_types),
            'description': self.faker.text(max_nb_chars=200),
            'requirements': self.faker.text(max_nb_chars=100)
        }
        self.create_job(data, employer)

    def list_all_jobs(self):
        """Displays a simplified summary of all created jobs"""
        print("\n🔹 **Job Listings:**")
        for job in Job.objects.all():
            employer_name = job.employer.username if job.employer else "No Employer"
            print(f"  ✅ {job.title} | {employer_name} | {job.job_type}")

    def create_favorite_jobs(self):
        """Creates some favorite job relationships for applicants"""
        print("\nCreating favorite jobs...")
        # Get some applicants and jobs to create favorites
        applicants = User.objects.filter(role="Applicant")[:3]  # First 3 applicants
        jobs = Job.objects.all()[:5]  # First 5 jobs
        
        for applicant in applicants:
            # Randomly select 2-3 jobs for each applicant
            for job in jobs[:random.randint(2, 3)]:
                FavoriteJob.objects.get_or_create(
                    user=applicant,
                    job=job
                )
            print(f"✅ Created favorites for {applicant.username}")

def create_username(first_name, last_name):
    return '@' + first_name.lower() + last_name.lower()

def create_email(first_name, last_name):
    return first_name.lower() + '@example.org'
