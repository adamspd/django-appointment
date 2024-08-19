from datetime import timedelta

from django.test import TestCase

from appointment.models import Appointment, AppointmentRequest, Service, StaffMember
from appointment.tests.mixins.base_mixin import (
    AppointmentMixin, AppointmentRequestMixin, AppointmentRescheduleHistoryMixin, ServiceMixin, StaffMemberMixin,
    UserMixin
)
from appointment.utils.db_helpers import get_user_model


class BaseTest(TestCase, UserMixin, StaffMemberMixin, ServiceMixin, AppointmentRequestMixin,
               AppointmentMixin, AppointmentRescheduleHistoryMixin):
    service1 = None
    service2 = None
    staff_member1 = None
    staff_member2 = None
    users = None

    USER_SPECS = {
        'staff1': {"first_name": "Daniel", "last_name": "Jackson", "email": "daniel.jackson@django-appointment.com",
                   "username": "daniel.jackson"},
        'staff2': {"first_name": "Samantha", "last_name": "Carter", "email": "samantha.carter@django-appointment.com",
                   "username": "samantha.carter"},
        'client1': {"first_name": "Georges", "last_name": "Hammond",
                    "email": "georges.s.hammond@django-appointment.com", "username": "georges.hammond"},
        'client2': {"first_name": "Tealc", "last_name": "Kree", "email": "tealc.kree@django-appointment.com",
                    "username": "tealc.kree"},
        'superuser': {"first_name": "Jack", "last_name": "O'Neill", "email": "jack-oneill@django-appointment.com",
                      "username": "jack.o.neill"},
    }

    @classmethod
    def setUpTestData(cls):
        cls.users = {key: cls.create_user_(**details) for key, details in cls.USER_SPECS.items()}
        cls.service1 = cls.create_service_(
            name="Stargate Activation", duration=timedelta(hours=1), price=100000, description="Activate the Stargate")
        cls.service2 = cls.create_service_(
            name="Dial Home Device Repair", duration=timedelta(hours=2), price=200000, description="Repair the DHD")
        # Mapping services to staff members
        cls.staff_member1 = cls.create_staff_member_(user=cls.users['staff1'], service=cls.service1)
        cls.staff_member2 = cls.create_staff_member_(user=cls.users['staff2'], service=cls.service2)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Clean up any class-level resources
        cls.clean_all_data()

    @classmethod
    def clean_all_data(cls):
        Appointment.objects.all().delete()
        AppointmentRequest.objects.all().delete()
        StaffMember.objects.all().delete()
        Service.objects.all().delete()
        get_user_model().objects.all().delete()

    def create_appt_request_for_sm1(self, service=None, staff_member=None, **kwargs):
        """Create an appointment request for staff_member1."""
        service = service or self.service1
        staff_member = staff_member or self.staff_member1
        return self.create_appointment_request_(service=service, staff_member=staff_member, **kwargs)

    def create_appt_request_for_sm2(self, service=None, staff_member=None, **kwargs):
        """Create an appointment request for staff_member2."""
        service = service or self.service2
        staff_member = staff_member or self.staff_member2
        return self.create_appointment_request_(service=service, staff_member=staff_member, **kwargs)

    def create_appt_for_sm1(self, appointment_request=None):
        if not appointment_request:
            appointment_request = self.create_appt_request_for_sm1()
        return self.create_appointment_(user=self.users['client1'], appointment_request=appointment_request)

    def create_appt_for_sm2(self, appointment_request=None):
        if not appointment_request:
            appointment_request = self.create_appt_request_for_sm2()
        return self.create_appointment_(user=self.users['client2'], appointment_request=appointment_request)

    def create_appt_reschedule_for_sm1(self, appointment_request=None, reason_for_rescheduling="Gate Malfunction"):
        if not appointment_request:
            appointment_request = self.create_appt_request_for_sm1()
        date_ = appointment_request.date + timedelta(days=7)
        return self.create_reschedule_history_(
            appointment_request=appointment_request,
            date_=date_,
            start_time=appointment_request.start_time,
            end_time=appointment_request.end_time,
            staff_member=appointment_request.staff_member,
            reason_for_rescheduling=reason_for_rescheduling,
        )

    def need_normal_login(self):
        self.client.force_login(self.create_user_())

    def need_staff_login(self):
        self.staff = self.users['staff1']
        self.staff.is_staff = True
        self.staff.save()
        self.client.force_login(self.staff)

    def need_superuser_login(self):
        self.superuser = self.users['superuser']
        self.superuser.is_superuser = True
        self.superuser.save()
        self.client.force_login(self.superuser)

    def clean_staff_member_objects(self, staff=None):
        """Delete all AppointmentRequests and Appointments linked to the StaffMember instance of self.user1."""
        if staff is None:
            staff = self.users['staff1']
        self.clean_appointment_for_user_(staff)
        self.clean_appt_request_for_user_(staff)
