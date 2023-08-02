import string

from django.test import TestCase

from appointment.models import EmailVerificationCode
from appointment.utils import Utility


class EmailVerificationCodeModelTestCase(TestCase):
    def setUp(self):
        self.user_model = Utility.get_user_model()
        self.user = self.user_model.objects.create_user(first_name="Tester",
                                                        email="testemail@gmail.com",
                                                        username="test_user", password="Kfdqi3!?n")
        self.code = EmailVerificationCode.generate_code(self.user)

    def test_code_creation(self):
        verification_code = EmailVerificationCode.objects.get(user=self.user)
        self.assertIsNotNone(verification_code)
        self.assertEqual(verification_code.code, self.code)

    def test_code_length(self):
        self.assertEqual(len(self.code), 6)

    def test_code_content(self):
        valid_characters = set(string.ascii_uppercase + string.digits)
        self.assertTrue(all(char in valid_characters for char in self.code))

    def test_code_str_representation(self):
        verification_code = EmailVerificationCode.objects.get(user=self.user)
        self.assertEqual(str(verification_code), self.code)

    def test_created_at(self):
        verification_code = EmailVerificationCode.objects.get(user=self.user)
        self.assertIsNotNone(verification_code.created_at)

    def test_updated_at(self):
        verification_code = EmailVerificationCode.objects.get(user=self.user)
        self.assertIsNotNone(verification_code.updated_at)
