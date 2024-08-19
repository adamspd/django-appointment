import datetime
from copy import deepcopy
from datetime import timedelta

from django.db import IntegrityError
from django.utils.translation import gettext as _

from appointment.models import Config, DayOff, Service, StaffMember, WorkingHours
from appointment.tests.base.base_test import BaseTest


class StaffMemberCreationTests(BaseTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.staff_member = cls.staff_member1
        cls.staff = cls.users['staff1']
        cls.service = cls.service1

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def test_default_attributes_on_creation(self):
        self.assertIsNotNone(self.staff_member)
        self.assertEqual(self.staff_member.user, self.staff)
        self.assertEqual(list(self.staff_member.get_services_offered()), [self.service])
        self.assertIsNone(self.staff_member.lead_time)
        self.assertIsNone(self.staff_member.finish_time)
        self.assertIsNone(self.staff_member.slot_duration)
        self.assertIsNone(self.staff_member.appointment_buffer_time)
        self.assertIsNotNone(self.staff_member.created_at)
        expected_str = self.staff_member.get_staff_member_name()
        self.assertEqual(str(self.staff_member), expected_str)

    def test_creation_without_service(self):
        """A staff member can be created without a service."""
        new_staff = self.create_user_(first_name="Jonas", last_name="Quinn", email="jonas.quinn@django-appointment.com",
                                      username="jonas.quinn")
        new_staff_member = StaffMember.objects.create(user=new_staff)
        self.assertIsNotNone(new_staff_member)
        self.assertEqual(new_staff_member.services_offered.count(), 0)

    def test_creation_fails_without_user(self):
        """A staff member cannot be created without a user."""
        with self.assertRaises(IntegrityError):
            StaffMember.objects.create()

    def test_get_staff_member_name_with_email(self):
        # Simulate create a staff member with only an email and username
        # (in my case, username is mandatory, but should work with email as well)
        email_only_user = self.create_user_(
                first_name="",
                last_name="",
                email="mckay.rodney@django-appointment.com",
                username="mckay.rodney@django-appointment.com"
        )
        email_only_staff = StaffMember.objects.create(user=email_only_user)

        # Test that the email is returned when no other name information is available
        self.assertEqual(email_only_staff.get_staff_member_name(), "mckay.rodney@django-appointment.com")

    def test_get_staff_member_name_priority(self):
        # Create a staff member with all name fields filled
        full_user = self.create_user_(
                first_name="Rodney",
                last_name="McKay",
                email="mckay.rodney@django-appointment.com",
                username="rodney.mckay"
        )
        full_staff = StaffMember.objects.create(user=full_user)

        # Test that the full name is returned when available
        self.assertEqual(full_staff.get_staff_member_name(), "Rodney McKay")

        # Modify the user to test different scenarios
        full_user.first_name = ""
        full_user.last_name = ""
        full_user.save()

        # Test that the username is returned when full name is not available
        self.assertEqual(full_staff.get_staff_member_name(), "rodney.mckay")

        full_user.username = ""
        full_user.save()

        # Test that the email is returned when username and full name are not available
        self.assertEqual(full_staff.get_staff_member_name(), "mckay.rodney@django-appointment.com")


class StaffMemberServiceTests(BaseTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.staff_member = cls.staff_member1
        cls.staff = cls.users['staff1']
        cls.service = cls.service1

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def get_fresh_staff_member(self):
        return deepcopy(self.staff_member)

    def test_association_with_multiple_services(self):
        """A staff member can offer multiple services."""
        ori = self.create_service_(name="Ori Shield Configuration", duration=timedelta(hours=1), price=100000,
                                   description="Configure the Ori shield")
        symbiote = self.create_service_(name="Symbiote Extraction", duration=timedelta(hours=1), price=100000,
                                        description="Extract a symbiote")
        sm = self.get_fresh_staff_member()

        sm.services_offered.add(ori)
        sm.services_offered.add(symbiote)

        self.assertIn(ori, sm.services_offered.all())
        self.assertIn(symbiote, sm.services_offered.all())

    def test_services_offered(self):
        """Test get_services_offered & get_service_offered_text function."""
        self.assertIn(self.service, self.staff_member.get_services_offered())
        self.assertEqual(self.staff_member.get_service_offered_text(), self.service.name)
        self.assertTrue(self.staff_member.get_service_is_offered(self.service.pk))

    def test_staff_member_with_non_existent_service(self):
        """A staff member cannot offer a non-existent service."""
        new_staff = self.create_user_(first_name="Vala", last_name="Mal Doran",
                                      email="vala.mal-doran@django-appointment.com", username="vala.mal-doran")
        new_staff_member = StaffMember.objects.create(user=new_staff)

        # Trying to add a non-existent service to the staff member's services_offered
        with self.assertRaises(ValueError):
            new_staff_member.services_offered.add(
                    Service(id=9999, name="Prometheus Acquisition", duration=timedelta(hours=2), price=200))


class StaffMemberWorkingTimeTests(BaseTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.staff_member = cls.staff_member1
        cls.staff = cls.users['staff1']
        cls.service = cls.service1

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def get_fresh_staff_member(self):
        return deepcopy(self.staff_member)

    def test_working_both_weekend_days(self):
        """Test works_on_both_weekends_day method."""
        sm = self.get_fresh_staff_member()
        sm.work_on_saturday = True
        sm.work_on_sunday = True
        self.assertTrue(sm.works_on_both_weekends_day())

    def test_get_non_working_days(self):
        """Test get_non_working_days method."""
        sm = self.get_fresh_staff_member()
        sm.work_on_saturday = False
        sm.work_on_sunday = False
        self.assertEqual(sm.get_non_working_days(), [6, 0])  # [6, 0] represents Saturday and Sunday respectively

    def test_identification_of_all_non_working_days(self):
        """Test various combinations of weekend work using a deepcopy of staff_member."""
        # Test with work on Saturday only
        sm = self.get_fresh_staff_member()

        sm.work_on_saturday = True
        sm.work_on_sunday = False
        sm.save()
        self.assertEqual(sm.get_weekend_days_worked_text(), _("Saturday"))

        # Test with work on both Saturday and Sunday
        sm.work_on_saturday = True
        sm.work_on_sunday = True
        sm.save()
        self.assertEqual(sm.get_weekend_days_worked_text(), _("Saturday and Sunday"))

        # Test with work on Sunday only
        sm.work_on_saturday = False
        sm.work_on_sunday = True
        sm.save()
        self.assertEqual(sm.get_weekend_days_worked_text(), _("Sunday"))

        # Test with work on neither Saturday nor Sunday
        sm.work_on_saturday = False
        sm.work_on_sunday = False
        sm.save()
        self.assertEqual(sm.get_weekend_days_worked_text(), _("None"))

    def test_get_days_off(self):
        """Test retrieval of days off."""
        sm = self.get_fresh_staff_member()
        DayOff.objects.create(staff_member=sm, start_date="2023-01-01", end_date="2023-01-02")
        self.assertEqual(len(sm.get_days_off()), 1)

    def test_get_working_hours(self):
        """Test retrieval of working hours."""
        sm = self.get_fresh_staff_member()
        WorkingHours.objects.create(staff_member=sm, day_of_week=1, start_time=datetime.time(9, 0),
                                    end_time=datetime.time(17, 0))
        self.assertEqual(len(sm.get_working_hours()), 1)

        # Precautionary cleanup (FIRST principle)
        WorkingHours.objects.all().delete()

    def test_update_upon_working_hours_deletion(self):
        """Test the update of work_on_saturday and work_on_sunday upon working-hours deletion."""
        sm = self.get_fresh_staff_member()
        sm.work_on_saturday = True
        sm.work_on_sunday = True
        sm.save()

        sm.update_upon_working_hours_deletion(6)
        self.assertFalse(sm.work_on_saturday)
        sm.update_upon_working_hours_deletion(0)
        self.assertFalse(sm.work_on_sunday)

    def test_is_working_day(self):
        """Test whether a day is considered a working day."""
        sm = self.get_fresh_staff_member()
        sm.work_on_saturday = False
        sm.work_on_sunday = False
        sm.save()

        self.assertFalse(self.staff_member.is_working_day(6))  # Saturday
        self.assertTrue(self.staff_member.is_working_day(1))  # Monday


class StaffMemberGetterTestCase(BaseTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.staff_member = cls.staff_member1
        cls.staff = cls.users['staff1']
        cls.service = cls.service1

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def get_fresh_staff_member(self):
        return deepcopy(self.staff_member)

    def test_get_staff_member_first_name(self):
        """Test that the staff member's first name is returned."""
        self.assertEqual(self.staff_member.get_staff_member_first_name(), self.staff.first_name)

    def test_config_values_takes_over_when_sm_values_null(self):
        """When some values are null in the StaffMember, the Config values should be used."""
        config = Config.objects.create(
                lead_time=datetime.time(9, 34),
                finish_time=datetime.time(17, 11),
                slot_duration=37,
                appointment_buffer_time=16
        )
        # Checking that the StaffMember's values are None
        self.assertIsNone(self.staff_member.slot_duration)
        self.assertIsNone(self.staff_member.lead_time)
        self.assertIsNone(self.staff_member.finish_time)
        self.assertIsNone(self.staff_member.appointment_buffer_time)

        # Checking that the Config values are used
        self.assertEqual(self.staff_member.get_slot_duration(), config.slot_duration)
        self.assertEqual(self.staff_member.get_lead_time(), config.lead_time)
        self.assertEqual(self.staff_member.get_finish_time(), config.finish_time)
        self.assertEqual(self.staff_member.get_appointment_buffer_time(), config.appointment_buffer_time)

        # Setting the StaffMember values
        sm = self.get_fresh_staff_member()
        sm.slot_duration = 45
        sm.lead_time = datetime.time(9, 0)
        sm.finish_time = datetime.time(17, 0)
        sm.appointment_buffer_time = 15

        # Checking that the StaffMember values are used and not the Config values
        self.assertEqual(sm.get_slot_duration(), 45)
        self.assertEqual(sm.get_lead_time(), datetime.time(9, 0))
        self.assertEqual(sm.get_finish_time(), datetime.time(17, 0))
        self.assertEqual(sm.get_appointment_buffer_time(), 15)

    def test_get_slot_duration_and_appt_buffer_time_text(self):
        """Test get_slot_duration_text & get_appointment_buffer_time_text function."""
        sm = self.get_fresh_staff_member()
        sm.slot_duration = 33
        sm.appointment_buffer_time = 24
        self.assertEqual(sm.get_slot_duration_text(), "33 minutes")
        self.assertEqual(sm.get_appointment_buffer_time_text(), "24 minutes")
