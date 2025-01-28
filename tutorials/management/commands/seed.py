from django.core.management.base import BaseCommand
from tutorials.models.user_model import User
from faker import Faker

user_fixtures = [
    {'username': '@damla', 'email': 'Damla@example.org', 'first_name': 'Damla', 'last_name': 'Sen', 'role': 'job_seeker'},
    {'username': '@tan', 'email': 'Tan@example.org', 'first_name': 'Tan', 'last_name': 'Yukseloglu', 'role': 'employer'},
    {'username': '@rares', 'email': 'Rares@example.org', 'first_name': 'Rares', 'last_name': 'Filimon', 'role': 'job_seeker'},
    {'username': '@mert', 'email': 'Mert@example.org', 'first_name': 'Mert', 'last_name': 'Johnson', 'role': 'employer'},
    {'username': '@jj', 'email': 'Jj@example.org', 'first_name': 'JJ', 'last_name': 'Zhou', 'role': 'job_seeker'},
    {'username': '@finn', 'email': 'Finn@example.org', 'first_name': 'Finn', 'last_name': 'Corney', 'role': 'employer'},
    {'username': '@liam', 'email': 'Liam@example.org', 'first_name': 'Liam', 'last_name': 'Ferran', 'role': 'job_seeker'},
    {'username': '@trong', 'email': 'Trong@example.org', 'first_name': 'Trong', 'last_name': 'Vu', 'role': 'job_seeker'},
    {'username': '@nehir', 'email': 'Nehir@example.org', 'first_name': 'Nehir', 'last_name': 'Evlimoglu', 'role': 'employer'},
]

class Command(BaseCommand):
    """Build automation command to seed the database."""

    USER_COUNT = 20
    EMPLOYER_COUNT = 5
    APPLICANT_COUNT = 25
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

    def create_users(self):
        self.generate_user_fixtures()
        self.generate_random_users()

    def generate_user_fixtures(self):
        for data in user_fixtures:
            self.try_create_user(data)

    def generate_random_users(self):
        user_count = User.objects.count()
        employer_count = User.objects.filter(role="Employer').count()
        applicant_count = User.objects.filter(role='Job Seeker').count()

        while user_count < self.USER_COUNT:
            print(f"Seeding user {user_count + 1}/{self.USER_COUNT}", end='\r')

            if employer_count < self.EMPLOYER_COUNT:
                self.generate_user('Employer')
                employer_count += 1
            else:
                self.generate_user('Job Seeker')
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


def create_username(first_name, last_name):
    return '@' + first_name.lower() + last_name.lower()

def create_email(first_name, last_name):
    return first_name.lower() + '@example.org'
