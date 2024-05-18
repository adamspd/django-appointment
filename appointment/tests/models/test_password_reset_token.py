import datetime
import time

from django.utils import timezone

from appointment.models import PasswordResetToken
from appointment.tests.base.base_test import BaseTest


class PasswordResetTokenCreationTests(BaseTest):

    def setUp(self):
        super().setUp()
        self.user = self.create_user_(username='janet.fraiser', email='janet.fraiser@django-appointment.com',
                                      password='LovedCassandra', first_name='Janet')
        self.expired_time = timezone.now() - datetime.timedelta(minutes=5)
        self.token = PasswordResetToken.create_token(user=self.user)

    def tearDown(self):
        super().tearDown()
        self.user.delete()
        self.token.delete()

    def test_default_attributes_on_creation(self):
        self.assertIsNotNone(self.token)
        self.assertFalse(self.token.is_expired)
        self.assertFalse(self.token.is_verified)

    def test_str_representation(self):
        """Test the string representation of the token."""
        expected_str = (f"Password reset token for {self.user} "
                        f"[{self.token.token} status: {self.token.status} expires at {self.token.expires_at}]")
        self.assertEqual(str(self.token), expected_str)


class PasswordResetTokenPropertiesTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.user = self.create_user_(username='janet.fraiser', email='janet.fraiser@django-appointment.com',
                                      password='LovedCassandra', first_name='Janet')
        self.expired_time = timezone.now() - datetime.timedelta(minutes=5)
        self.token = PasswordResetToken.create_token(user=self.user)

    def tearDown(self):
        super().tearDown()
        self.user.delete()
        self.token.delete()

    def test_is_verified_property(self):
        """Test the is_verified property to check if the token status is correctly identified as verified."""
        token = PasswordResetToken.create_token(self.user)
        self.assertFalse(token.is_verified, "Newly created token should not be verified.")
        token.mark_as_verified()
        self.assertTrue(token.is_verified, "Token should be marked as verified after calling mark_as_verified.")

    def test_is_active_property(self):
        """Test the is_active property to check if the token status is correctly identified as active."""
        token = PasswordResetToken.create_token(self.user)
        self.assertTrue(token.is_active, "Newly created token should be active.")
        token.mark_as_verified()
        token.refresh_from_db()
        self.assertFalse(token.is_active, "Token should not be active after being verified.")

        # Invalidate the token and check is_active property
        token.status = PasswordResetToken.TokenStatus.INVALIDATED
        token.save()
        self.assertFalse(token.is_active, "Token should not be active after being invalidated.")

    def test_is_invalidated_property(self):
        """Test the is_invalidated property to check if the token status is correctly identified as invalidated."""
        token = PasswordResetToken.create_token(self.user)
        self.assertFalse(token.is_invalidated, "Newly created token should not be invalidated.")

        # Invalidate the token and check is_invalidated property
        token.status = PasswordResetToken.TokenStatus.INVALIDATED
        token.save()
        self.assertTrue(token.is_invalidated, "Token should be marked as invalidated after status change.")

    def test_token_expiration(self):
        """Test that a token is considered expired after the expiration time."""
        token = PasswordResetToken.create_token(user=self.user, expiration_minutes=-1)  # Token already expired
        self.assertTrue(token.is_expired)


class PasswordResetTokenVerificationTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.user = self.create_user_(username='janet.fraiser', email='janet.fraiser@django-appointment.com',
                                      password='LovedCassandra', first_name='Janet')
        self.expired_time = timezone.now() - datetime.timedelta(minutes=5)

    def test_verify_token_success(self):
        """Test successful token verification."""
        token = PasswordResetToken.create_token(user=self.user)
        verified_token = PasswordResetToken.verify_token(user=self.user, token=token.token)
        self.assertIsNotNone(verified_token)

    def test_verify_token_failure_expired(self):
        """Test token verification fails if the token has expired."""
        token = PasswordResetToken.create_token(user=self.user, expiration_minutes=-1)  # Token already expired
        verified_token = PasswordResetToken.verify_token(user=self.user, token=token.token)

        self.assertIsNone(verified_token, "Expired token should not verify")

    def test_verify_token_failure_wrong_user(self):
        """Test token verification fails if the token does not belong to the given user."""
        another_user = self.create_user_(username='another_user', email='another@example.com',
                                         password='test_pass456')
        token = PasswordResetToken.create_token(user=self.user)
        verified_token = PasswordResetToken.verify_token(user=another_user, token=token.token)
        self.assertIsNone(verified_token)

    def test_verify_token_failure_already_verified(self):
        """Test token verification fails if the token has already been verified."""
        token = PasswordResetToken.create_token(user=self.user)
        token.mark_as_verified()
        verified_token = PasswordResetToken.verify_token(user=self.user, token=token.token)
        self.assertIsNone(verified_token)

    def test_verify_token_invalid_token(self):
        """Test token verification fails if the token does not exist."""
        PasswordResetToken.create_token(user=self.user)
        invalid_token_uuid = "12345678-1234-1234-1234-123456789012"  # An invalid token UUID
        verified_token = PasswordResetToken.verify_token(user=self.user, token=invalid_token_uuid)
        self.assertIsNone(verified_token)

    def test_token_expiration_boundary(self):
        """Test token verification at the exact moment of expiration."""
        token = PasswordResetToken.create_token(user=self.user, expiration_minutes=0)  # Token expires now
        # Assuming there might be a very slight delay before verification, we wait a second
        time.sleep(1)
        verified_token = PasswordResetToken.verify_token(user=self.user, token=token.token)
        self.assertIsNone(verified_token)

    def test_create_multiple_tokens_for_user(self):
        """Test that multiple tokens can be created for a single user and only the latest is valid."""
        old_token = PasswordResetToken.create_token(user=self.user)
        new_token = PasswordResetToken.create_token(user=self.user)

        old_verified = PasswordResetToken.verify_token(user=self.user, token=old_token.token)
        new_verified = PasswordResetToken.verify_token(user=self.user, token=new_token.token)

        self.assertIsNone(old_verified, "Old token should not be valid after creating a new one")
        self.assertIsNotNone(new_verified, "New token should be valid")

    def test_token_verification_resets_after_expiration(self):
        """Test that an expired token cannot be verified after its expiration, even if marked as verified."""
        token = PasswordResetToken.create_token(user=self.user, expiration_minutes=-1)  # Already expired
        token.mark_as_verified()

        verified_token = PasswordResetToken.verify_token(user=self.user, token=token.token)
        self.assertIsNone(verified_token, "Expired token should not verify, even if marked as verified")

    def test_verify_token_invalidated(self):
        """Test token verification fails if the token has been invalidated."""
        token = PasswordResetToken.create_token(self.user)
        # Invalidate the token by creating a new one
        PasswordResetToken.create_token(self.user)
        verified_token = PasswordResetToken.verify_token(self.user, token.token)
        self.assertIsNone(verified_token)

    def test_expired_token_verification(self):
        """Test that an expired token cannot be verified."""
        token = PasswordResetToken.objects.create(user=self.user, expires_at=self.expired_time,
                                                  status=PasswordResetToken.TokenStatus.ACTIVE)
        self.assertTrue(token.is_expired)
        verified_token = PasswordResetToken.verify_token(self.user, token.token)
        self.assertIsNone(verified_token, "Expired token should not verify")

    def test_token_verification_after_user_deletion(self):
        """Test that a token cannot be verified after the associated user is deleted."""
        token = PasswordResetToken.create_token(self.user)
        self.user.delete()
        verified_token = PasswordResetToken.verify_token(None, token.token)
        self.assertIsNone(verified_token, "Token should not verify after user deletion")


class PasswordResetTokenTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.user = self.create_user_(username='janet.fraiser', email='janet.fraiser@django-appointment.com',
                                      password='LovedCassandra', first_name='Janet')
        self.expired_time = timezone.now() - datetime.timedelta(minutes=5)

    def tearDown(self):
        super().tearDown()
        PasswordResetToken.objects.all().delete()
        self.user.delete()

    def test_mark_as_verified(self):
        """Test marking a token as verified."""
        token = PasswordResetToken.create_token(user=self.user)
        self.assertFalse(token.is_verified)
        token.mark_as_verified()
        token.refresh_from_db()  # Refresh the token object from the database
        self.assertTrue(token.is_verified)

    def test_mark_as_verified_is_idempotent(self):
        """Test that marking a token as verified multiple times has no adverse effect."""
        token = PasswordResetToken.create_token(user=self.user)
        token.mark_as_verified()
        first_verification_time = token.updated_at

        time.sleep(1)  # Ensure time has passed
        token.mark_as_verified()
        token.refresh_from_db()

        self.assertTrue(token.is_verified)
        self.assertEqual(first_verification_time, token.updated_at,
                         "Token verification time should not update on subsequent calls")

    def test_deleting_user_cascades_to_tokens(self):
        """Test that deleting a user deletes associated password reset tokens."""

        apophis = self.create_user_(username='apophis.false_god', email='apophis.false_god@django-appointment.com',
                                    password='LovedSayingSholva', first_name='Apophis')
        token = PasswordResetToken.create_token(user=apophis)
        apophis.delete()

        with self.assertRaises(PasswordResetToken.DoesNotExist):
            PasswordResetToken.objects.get(pk=token.pk)
