import datetime

from appointment.tests.base.base_test import BaseTest
from appointment.utils.db_helpers import WorkingHours
from appointment.utils.permissions import check_permissions, check_extensive_permissions, check_entity_ownership


class PermissionTests(BaseTest):

    def setUp(self):
        super().setUp()
        # Create users and entities for testing-
        self.superuser = self.create_user_(username='superuser', email="superuser@gmail.com")
        self.superuser.is_superuser = True
        self.superuser.save()
        self.entity_owned_by_user1 = WorkingHours.objects.create(staff_member=self.staff_member1, day_of_week=0,
                                                                 start_time=datetime.time(8, 0),
                                                                 end_time=datetime.time(12, 0))

    def test_check_entity_ownership(self):
        """Test if ownership of an entity can be checked."""
        # User is the owner
        self.assertTrue(check_entity_ownership(self.user1, self.entity_owned_by_user1))

        # Superuser but not owner
        self.assertTrue(check_entity_ownership(self.superuser, self.entity_owned_by_user1))

        # Neither owner nor superuser
        self.assertFalse(check_entity_ownership(self.user2, self.entity_owned_by_user1))

    def test_check_extensive_permissions(self):
        """Test if extensive permissions can be checked."""
        # staff_user_id matches and user owns entity
        self.assertTrue(check_extensive_permissions(self.user1.pk, self.user1, self.entity_owned_by_user1))

        # staff_user_id matches but user doesn't own entity
        self.assertFalse(check_extensive_permissions(self.user2.pk, self.user2, self.entity_owned_by_user1))

        # staff_user_id doesn't match but user is superuser
        self.assertTrue(check_extensive_permissions(None, self.superuser, self.entity_owned_by_user1))

        # staff_user_id matches and no entity provided
        self.assertTrue(check_extensive_permissions(self.user1.pk, self.user1, None))

        # Neither staff_user_id matches nor superuser
        self.assertFalse(check_extensive_permissions(None, self.user2, self.entity_owned_by_user1))

    def test_check_permissions(self):
        """Test if permissions can be checked."""
        # staff_user_id matches
        self.assertTrue(check_permissions(self.user1.pk, self.user1))

        # staff_user_id doesn't match but user is superuser
        self.assertTrue(check_permissions(None, self.superuser))

        # Neither staff_user_id matches nor superuser
        self.assertFalse(check_permissions(None, self.user2))
