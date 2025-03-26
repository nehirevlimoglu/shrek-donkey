from django.test import TestCase
from django.contrib.auth import get_user_model
from tutorials.models.admin_models import Admin
from tutorials.forms.admin_forms import AdminProfileForm

User = get_user_model()

class AdminProfileFormTest(TestCase):
    def setUp(self):
        # Create a test admin user.
        self.user = User.objects.create_user(
            username="admin1",
            email="admin1@test.com",
            password="password123",
            first_name="John",
            last_name="Doe",
            role="Admin"
        )
        # Create the Admin instance linked to the user.
        self.admin = Admin.objects.create(
            user=self.user,
            phone_number="+1234567890"
        )
        # Data for updating the profile.
        self.valid_data = {
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@smith.com",
            "phone_number": "+9876543210"
        }
        self.new_data = {
            "first_name": "Bob",
            "last_name": "Marley",
            "email": "bob@marley.com",
            "phone_number": "+1112223333"
        }

    def test_initial_values(self):
        """
        Test that the form's initial values for first_name, last_name, and email
        are populated from the linked User.
        """
        form = AdminProfileForm(user=self.user, instance=self.admin)
        self.assertEqual(form.fields['first_name'].initial, self.user.first_name)
        self.assertEqual(form.fields['last_name'].initial, self.user.last_name)
        self.assertEqual(form.fields['email'].initial, self.user.email)
        # Phone number comes from the Admin instance.
        self.assertEqual(form.initial.get('phone_number', None), self.admin.phone_number)

    def test_save_updates_user_with_commit_true(self):
        """
        Test that saving with commit=True updates both the Admin instance and the
        linked User instance.
        """
        form = AdminProfileForm(data=self.new_data, instance=self.admin, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        admin_instance = form.save(commit=True)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Bob")
        self.assertEqual(self.user.last_name, "Marley")
        self.assertEqual(self.user.email, "bob@marley.com")
        self.assertEqual(admin_instance.phone_number, self.new_data["phone_number"])

    def test_save_no_commit(self):
        """
        Test that saving with commit=False does not immediately persist changes to the
        linked User in the database.
        """
        form = AdminProfileForm(data=self.new_data, instance=self.admin, user=self.user)
        self.assertTrue(form.is_valid(), form.errors)
        admin_instance = form.save(commit=False)
        # The in-memory admin_instance reflects the new phone number.
        self.assertEqual(admin_instance.phone_number, self.new_data["phone_number"])
        # But the related User is not updated in the DB yet.
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "John")
        self.assertEqual(self.user.last_name, "Doe")
        self.assertEqual(self.user.email, "admin1@test.com")
        # Note: calling admin_instance.save() alone does NOT update the User,
        # because the form only saves the user when commit=True.

    def test_init_without_user(self):
        """
        Test that form initializes without errors even if no user is provided.
        Ensures the `if self.user` block is skipped gracefully.
        """
        form = AdminProfileForm(instance=self.admin)
        self.assertIsNone(form.fields['first_name'].initial)
        self.assertIsNone(form.fields['last_name'].initial)
        self.assertIsNone(form.fields['email'].initial)

    def test_save_without_user(self):
        """
        Ensure that the save method works correctly when no user is passed.
        Only Admin model should be saved.
        """
        form = AdminProfileForm(data=self.valid_data, instance=self.admin)
        self.assertTrue(form.is_valid())
        admin_instance = form.save(commit=True)
        self.user.refresh_from_db()
        # User should not be updated
        self.assertEqual(self.user.first_name, "John")
        self.assertEqual(admin_instance.phone_number, self.valid_data["phone_number"])

