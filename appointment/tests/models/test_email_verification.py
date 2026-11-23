import datetime
import string

from django.test import TestCase
from django.utils import timezone

from appointment.models import EmailVerificationCode
from appointment.tests.mixins.base_mixin import UserMixin


class EmailVerificationCodeBasicTestCase(TestCase, UserMixin):
    def setUp(self):
        self.user = self.create_user_()
        self.code = EmailVerificationCode.generate_code(self.user)

    def tearDown(self):
        super().tearDown()
        EmailVerificationCode.objects.all().delete()
        self.user.delete()

    def test_default_attributes_on_creation(self):
        """Test if a verification code can be generated."""
        verification_code = EmailVerificationCode.objects.get(user=self.user)
        self.assertIsNotNone(verification_code)
        self.assertEqual(verification_code.code, self.code)
        self.assertEqual(str(verification_code), self.code)
        self.assertIsNotNone(verification_code.created_at)
        self.assertIsNotNone(verification_code.updated_at)
        self.assertEqual(len(self.code), 6)

    def test_code_content(self):
        """Test that the code only contains uppercase letters and digits."""
        valid_characters = set(string.ascii_uppercase + string.digits)
        self.assertTrue(all(char in valid_characters for char in self.code))

    def test_new_code_replaces_old_one(self):
        """A user has one code at a time: a new code replaces the old one."""
        new_code = EmailVerificationCode.generate_code(self.user)
        self.assertEqual(list(EmailVerificationCode.objects.filter(user=self.user).values_list('code', flat=True)),
                         [new_code])
        if new_code != self.code:
            self.assertFalse(EmailVerificationCode.verify(self.user, self.code))
        self.assertTrue(EmailVerificationCode.verify(self.user, new_code))

    def test_verify_accepts_valid_code_once(self):
        self.assertTrue(EmailVerificationCode.verify(self.user, self.code))
        self.assertFalse(EmailVerificationCode.verify(self.user, self.code))
        self.assertFalse(EmailVerificationCode.objects.filter(user=self.user).exists())

    def test_verify_ignores_case_and_spaces(self):
        self.assertTrue(EmailVerificationCode.verify(self.user, f" {self.code.lower()} "))

    def test_verify_rejects_expired_code(self):
        EmailVerificationCode.objects.filter(user=self.user).update(
            created_at=timezone.now() - datetime.timedelta(minutes=11))
        self.assertFalse(EmailVerificationCode.verify(self.user, self.code))

    def test_verify_rejects_empty_values(self):
        self.assertFalse(EmailVerificationCode.verify(self.user, ''))
        self.assertFalse(EmailVerificationCode.verify(self.user, None))
        self.assertFalse(EmailVerificationCode.verify(None, self.code))

    def test_verify_rejects_non_ascii_input(self):
        self.assertFalse(EmailVerificationCode.verify(self.user, 'ÀÉÎ123'))

    def test_code_is_dropped_after_too_many_wrong_tries(self):
        wrong = 'AAAAAA' if self.code != 'AAAAAA' else 'BBBBBB'
        for _i in range(EmailVerificationCode.MAX_ATTEMPTS):
            self.assertFalse(EmailVerificationCode.verify(self.user, wrong))
        self.assertFalse(EmailVerificationCode.verify(self.user, self.code))

    def test_wrong_tries_are_counted(self):
        wrong = 'AAAAAA' if self.code != 'AAAAAA' else 'BBBBBB'
        EmailVerificationCode.verify(self.user, wrong)
        EmailVerificationCode.verify(self.user, wrong)
        self.assertEqual(EmailVerificationCode.objects.get(user=self.user).attempts, 2)
        self.assertTrue(EmailVerificationCode.verify(self.user, self.code))

    def test_code_verification_match(self):
        """The check_code method returns True when the code matches."""
        code = EmailVerificationCode.objects.get(user=self.user)
        self.assertTrue(code.check_code(self.code))

    def test_code_verification_mismatch(self):
        """The check_code method returns False when the code does not match."""
        mismatched_code = "ABCDEF"
        code = EmailVerificationCode.objects.get(user=self.user)
        self.assertFalse(code.check_code(mismatched_code))

    def test_code_for_a_new_address(self):
        code = EmailVerificationCode.generate_code(None, email='new@django-appointment.com')
        self.assertFalse(EmailVerificationCode.verify(None, code, email='other@django-appointment.com'))
        self.assertFalse(EmailVerificationCode.verify(None, code))
        self.assertTrue(EmailVerificationCode.verify(None, code, email='NEW@django-appointment.com'))
