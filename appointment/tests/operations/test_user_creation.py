from django.test import TestCase

from appointment.utils import Utility
from appointment.views import create_new_user


class CreateNewUserTest(TestCase):

    def test_create_new_user_unique_username(self):
        client_data = {'name': 'John Doe', 'email': 'john.doe@example.com'}
        user = create_new_user(client_data)
        self.assertEqual(user.username, 'john.doe')
        self.assertEqual(user.first_name, 'John Doe')
        self.assertEqual(user.email, 'john.doe@example.com')

    def test_create_new_user_duplicate_username(self):
        client_data1 = {'name': 'John Doe', 'email': 'john.doe@example.com'}
        user1 = create_new_user(client_data1)
        self.assertEqual(user1.username, 'john.doe')

        client_data2 = {'name': 'Jane Doe', 'email': 'john.doe@example.com'}
        user2 = create_new_user(client_data2)
        self.assertEqual(user2.username, 'john.doe01')  # Suffix added

        client_data3 = {'name': 'James Doe', 'email': 'john.doe@example.com'}
        user3 = create_new_user(client_data3)
        self.assertEqual(user3.username, 'john.doe02')  # Next suffix

    def test_create_new_user_check_password(self):
        client_data = {'name': 'John Doe', 'email': 'john.doe@example.com'}
        user = create_new_user(client_data)
        password = f"{Utility.get_website_name()}{Utility.get_current_year()}"
        self.assertTrue(user.check_password(password))
