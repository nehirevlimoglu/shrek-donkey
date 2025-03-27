from django.test import TestCase
from datetime import datetime, date
from tutorials.views.employer_views import calculate_duration

class DurationCalculationTests(TestCase):
    """Test suite for duration calculation functionality"""

    def test_calculate_duration_with_valid_dates(self):
        """Test duration calculation with valid start and end dates"""
        start_date = date(2020, 1, 1)
        end_date = date(2023, 6, 15)
        duration = calculate_duration(start_date, end_date)
        self.assertEqual(duration, "3 years, 5 months, 16 days")

    def test_calculate_duration_with_present(self):
        """Test duration calculation when end date is 'Present'"""
        start_date = date(2022, 1, 1)
        duration = calculate_duration(start_date, "Present")
        # Since this uses today's date, we just verify the format
        self.assertTrue("years" in duration)
        self.assertTrue("months" in duration)
        self.assertTrue("days" in duration)

    def test_calculate_duration_with_string_dates(self):
        """Test duration calculation with string date inputs"""
        start_date = "2021-01-01"
        end_date = "2022-01-01"
        duration = calculate_duration(start_date, end_date)
        self.assertEqual(duration, "1 years, 0 months, 0 days")

    def test_calculate_duration_with_invalid_dates(self):
        """Test duration calculation with invalid date formats"""
        # Test with invalid start date
        duration = calculate_duration("invalid-date", "2022-01-01")
        self.assertEqual(duration, "")

        # Test with invalid end date
        duration = calculate_duration("2022-01-01", "invalid-date")
        # Should use today's date as fallback
        self.assertTrue("years" in duration)
        self.assertTrue("months" in duration)
        self.assertTrue("days" in duration)

    def test_calculate_duration_with_missing_dates(self):
        """Test duration calculation with missing dates"""
        # Test with missing start date
        duration = calculate_duration(None, "2022-01-01")
        self.assertEqual(duration, "")

        # Test with missing end date
        start_date = date(2022, 1, 1)
        duration = calculate_duration(start_date, None)
        # Should calculate duration until today
        self.assertTrue("years" in duration)
        self.assertTrue("months" in duration)
        self.assertTrue("days" in duration)

    def test_calculate_duration_same_dates(self):
        """Test duration calculation when start and end dates are the same"""
        test_date = date(2023, 1, 1)
        duration = calculate_duration(test_date, test_date)
        self.assertEqual(duration, "0 years, 0 months, 0 days") 