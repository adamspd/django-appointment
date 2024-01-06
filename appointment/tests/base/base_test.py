from django.test import TestCase

from appointment.tests.mixins.base_mixin import (AppointmentMixin, AppointmentRequestMixin, ServiceMixin,
                                                 StaffMemberMixin, UserMixin)


class BaseTest(TestCase, UserMixin, StaffMemberMixin, ServiceMixin, AppointmentRequestMixin, AppointmentMixin):
    def setUp(self):
        # Users
        self.user1 = self.create_user_(email="tester1@gmail.com", username="tester1")
        self.user2 = self.create_user_(first_name="Tester2", email="tester2@gmail.com", username="tester2")
        self.client1 = self.create_user_(first_name="Client1", email="client1@gmail.com", username="client1")
        self.client2 = self.create_user_(first_name="Client2", email="client2@gmail.com", username="client2")

        # Services
        self.service1 = self.create_service_()
        self.service2 = self.create_service_(name="Service 2")

        # Staff Members
        self.staff_member1 = self.create_staff_member_(user=self.user1, service=self.service1)
        self.staff_member2 = self.create_staff_member_(user=self.user2, service=self.service2)

    def create_appt_request_for_sm1(self, **kwargs):
        """Create an appointment request for staff_member1."""
        return self.create_appointment_request_(service=self.service1, staff_member=self.staff_member1, **kwargs)

    def create_appt_request_for_sm2(self, **kwargs):
        """Create an appointment request for staff_member2."""
        return self.create_appointment_request_(service=self.service2, staff_member=self.staff_member2, **kwargs)

    def create_appointment_for_user1(self, appointment_request=None):
        if not appointment_request:
            appointment_request = self.create_appt_request_for_sm1()
        return self.create_appointment_(user=self.client1, appointment_request=appointment_request)

    def create_appointment_for_user2(self, appointment_request=None):
        if not appointment_request:
            appointment_request = self.create_appt_request_for_sm2()
        return self.create_appointment_(user=self.client2, appointment_request=appointment_request)
