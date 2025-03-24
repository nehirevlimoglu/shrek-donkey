import unittest
from datetime import date, datetime, timedelta
from tutorials.views.employer_views import calculate_duration  # Adjust the import path as needed

class CalculateDurationTests(unittest.TestCase):

    def test_no_start_date(self):
        """Test that if start_date is None, the function returns an empty string."""
        self.assertEqual(calculate_duration(None, "2020-01-01"), "")

    def test_invalid_start_date(self):
        """Test that an invalid start_date string returns an empty string."""
        self.assertEqual(calculate_duration("invalid-date", "2020-01-01"), "")

    def test_end_date_present(self):
        """Test that if end_date is 'Present', the function uses today's date."""
        start = "2020-01-01"
        today = date.today()
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        delta = today - start_date
        years = delta.days // 365
        months = (delta.days % 365) // 30
        days = (delta.days % 365) % 30
        expected = f"{years} years, {months} months, {days} days"
        self.assertEqual(calculate_duration(start, "Present"), expected)

    def test_end_date_empty(self):
        """Test that if end_date is empty, the function uses today's date."""
        start = "2020-01-01"
        today = date.today()
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
        delta = today - start_date
        years = delta.days // 365
        months = (delta.days % 365) // 30
        days = (delta.days % 365) % 30
        expected = f"{years} years, {months} months, {days} days"
        self.assertEqual(calculate_duration(start, ""), expected)

    def test_valid_dates_as_strings(self):
        """Test that providing valid start and end dates as strings returns the correct duration."""
        start = "2018-01-01"
        end = "2020-01-01"
        # 2018-01-01 to 2020-01-01 is 2 years, 0 months, 0 days based on our approximations.
        expected = "2 years, 0 months, 0 days"
        self.assertEqual(calculate_duration(start, end), expected)

    def test_valid_dates_as_date_objects(self):
        """Test that providing start and end dates as date objects returns the correct duration."""
        start = date(2018, 1, 1)
        end = date(2020, 1, 1)
        expected = "2 years, 0 months, 0 days"
        self.assertEqual(calculate_duration(start, end), expected)

if __name__ == '__main__':
    unittest.main()
