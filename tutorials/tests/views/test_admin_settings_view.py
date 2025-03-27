from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages

from tutorials.models.admin_models import Admin
from tutorials.forms.admin_forms import AdminProfileForm
from tutorials.forms.forms import CustomPasswordChangeForm

User = get_user_model()

class AdminSettingsViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = 'TestPass123!'
        self.user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password=self.password,
            role='Admin'
        )
        self.admin = Admin.objects.create(
            user=self.user,
            username='adminuser',
            email='admin@example.com',
            first_name='Admin',
            last_name='User'
        )
        self.client.login(username='adminuser', password=self.password)
        self.url = reverse('admin_settings')

    def test_default_tab_is_profile(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['tab'], 'profile')

    def test_get_change_profile_tab(self):
        response = self.client.get(self.url + '?tab=change-profile')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], AdminProfileForm)

    def test_post_change_profile_success(self):
        data = {
            'email': 'newemail@example.com',
            'username': 'adminuser',
            'first_name': 'Updated',
            'last_name': 'Admin'
        }
        response = self.client.post(self.url + '?tab=change-profile', data, follow=True)
        self.assertRedirects(response, self.url)
        self.admin.refresh_from_db()
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'newemail@example.com')

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Admin profile updated successfully." in str(m) for m in messages))

    def test_get_password_change_tab(self):
        response = self.client.get(self.url + '?tab=password')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['form'], CustomPasswordChangeForm)

    def test_post_password_change_success(self):
        new_password = 'NewSecurePassword123'
        data = {
            'old_password': self.password,
            'new_password1': new_password,
            'new_password2': new_password
        }
        response = self.client.post(self.url + '?tab=password', data, follow=True)
        self.assertRedirects(response, self.url)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Password changed successfully." in str(m) for m in messages))

    def test_invalid_password_change(self):
        data = {
            'old_password': 'wrongpassword',
            'new_password1': 'NewPassword123',
            'new_password2': 'NewPassword123'
        }
        response = self.client.post(self.url + '?tab=password', data)
        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertIn('old_password', form.errors)
        self.assertIn('Your old password was entered incorrectly', form.errors['old_password'][0])


    def test_invalid_profile_form(self):
        data = {
            'email': '',  # Allowed to be blank
            'username': 'adminuser',
            'first_name': 'Updated',
            'last_name': 'Admin'
        }
        response = self.client.post(self.url + '?tab=change-profile', data, follow=True)

        # Expect redirect because the form is still valid
        self.assertRedirects(response, self.url)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any("Admin profile updated successfully." in str(m) for m in messages))
