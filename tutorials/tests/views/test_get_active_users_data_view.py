from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

class GetActiveUsersDataViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create an admin user with the necessary flags
        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="password123",
            role="Admin",
            is_staff=True,
            is_superuser=True
        )
        self.client.force_login(self.admin_user)
        self.url = reverse("get_active_users_data")
        self.today = timezone.now().date()

        # For the 'day' branch, create 7 users with last_login on each of the past 7 days.
        now = timezone.now()
        for i in range(7):
            User.objects.create_user(
                username=f"active_day_{i}",
                email=f"active_day_{i}@example.com",
                password="pass",
                role="Applicant",
                last_login=now - timedelta(days=i)
            )

    def test_redirect_if_not_logged_in(self):
        """Test that non-logged-in users are redirected to the login page."""
        self.client.logout()
        response = self.client.get(self.url)
        expected_redirect = reverse("log_in") + "?next=" + self.url
        self.assertRedirects(response, expected_redirect)

    def test_active_users_day(self):
        """Test that 'period=day' returns data for the past 7 days."""
        response = self.client.get(self.url, {"period": "day"})
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        # Expect 7 labels and 7 values
        self.assertIn("labels", json_data)
        self.assertIn("values", json_data)
        self.assertEqual(len(json_data["labels"]), 7)
        self.assertEqual(len(json_data["values"]), 7)
        # Optionally, ensure the labels are abbreviated weekday names (e.g., 'Mon', 'Tue', etc.)
        for label in json_data["labels"]:
            self.assertTrue(isinstance(label, str))
        # And that values are non-negative integers
        for value in json_data["values"]:
            self.assertTrue(isinstance(value, int))
            self.assertGreaterEqual(value, 0)

    def test_active_users_week(self):
        """Test that 'period=week' returns data for the past 4 weeks."""
        response = self.client.get(self.url, {"period": "week"})
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        # Expect 4 labels and 4 values
        self.assertIn("labels", json_data)
        self.assertIn("values", json_data)
        self.assertEqual(len(json_data["labels"]), 4)
        self.assertEqual(len(json_data["values"]), 4)

    def test_active_users_month(self):
        """Test that 'period=month' returns data for the past 12 months."""
        # Create additional users for past months.
        now = timezone.now()
        for i in range(1, 13):
            # Create a user with last_login approximately 30*i days ago.
            User.objects.create_user(
                username=f"active_month_{i}",
                email=f"active_month_{i}@example.com",
                password="pass",
                role="Applicant",
                last_login=now - timedelta(days=30 * i)
            )
        response = self.client.get(self.url, {"period": "month"})
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertIn("labels", json_data)
        self.assertIn("values", json_data)
        # Expect 12 labels and 12 values
        self.assertEqual(len(json_data["labels"]), 12)
        self.assertEqual(len(json_data["values"]), 12)

    def test_invalid_period(self):
        """Test that an invalid period returns a 400 error with an error message."""
        response = self.client.get(self.url, {"period": "invalid"})
        self.assertEqual(response.status_code, 400)
        json_data = response.json()
        self.assertIn("error", json_data)
