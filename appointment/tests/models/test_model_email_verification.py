import string

from django.test import TestCase

from appointment.models import EmailVerificationCode
from appointment.tests.mixins.base_mixin import UserMixin


class EmailVerificationCodeModelTestCase(TestCase, UserMixin):
    def setUp(self):
        self.user = self.create_user_()
        self.code = EmailVerificationCode.generate_code(self.user)

    def test_code_creation(self):
        """Test if a verification code can be generated."""
        verification_code = EmailVerificationCode.objects.get(user=self.user)
        self.assertIsNotNone(verification_code)
        self.assertEqual(verification_code.code, self.code)

    def test_code_length(self):
        """Test that the code is six characters long."""
        self.assertEqual(len(self.code), 6)

    def test_code_content(self):
        """Test that the code only contains uppercase letters and digits."""
        valid_characters = set(string.ascii_uppercase + string.digits)
        self.assertTrue(all(char in valid_characters for char in self.code))

    def test_code_str_representation(self):
        """Test that the string representation of a verification code is correct."""
        verification_code = EmailVerificationCode.objects.get(user=self.user)
        self.assertEqual(str(verification_code), self.code)

    def test_created_at(self):
        """Test if the created_at field is set when a code is generated."""
        verification_code = EmailVerificationCode.objects.get(user=self.user)
        self.assertIsNotNone(verification_code.created_at)

    def test_updated_at(self):
        """Test if the updated_at field is set when a code is generated."""
        verification_code = EmailVerificationCode.objects.get(user=self.user)
        self.assertIsNotNone(verification_code.updated_at)

    def test_multiple_codes_for_user(self):
        """
        Test if multiple verification codes can be generated for a user.
        This should ideally create a new code, but the old one will still exist.
        """
        new_code = EmailVerificationCode.generate_code(self.user)
        self.assertNotEqual(self.code, new_code)

    def test_code_verification_match(self):
        """The check_code method returns True when the code matches."""
        code = EmailVerificationCode.objects.get(user=self.user)
        self.assertTrue(code.check_code(self.code))

    def test_code_verification_mismatch(self):
        """The check_code method returns False when the code does not match."""
        mismatched_code = "ABCDEF"
        code = EmailVerificationCode.objects.get(user=self.user)
        self.assertFalse(code.check_code(mismatched_code))
