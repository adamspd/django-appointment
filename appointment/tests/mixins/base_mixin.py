from datetime import date, time, timedelta

from appointment.models import (
    Appointment, AppointmentRequest, AppointmentRescheduleHistory, Config, Service, StaffMember
)
from appointment.utils.db_helpers import get_user_model


class UserMixin:
    def __init__(self):
        pass

    @classmethod
    def create_user_(cls, first_name="Janet", last_name="Fraiser", email="janet.fraiser@django-appointment.com",
                     username="janet.fraiser",
                     password="G0a'uld$Emp1re"):
        return get_user_model().objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
                password=password
        )


class ServiceMixin:
    def __init__(self):
        pass

    @classmethod
    def create_service_(cls, name="Quantum Mirror Assessment", duration=timedelta(hours=1), price=50000,
                        description="Assess the Quantum Mirror"):
        return Service.objects.create(
                name=name,
                duration=duration,
                price=price,
                description=description
        )


class StaffMemberMixin:
    def __init__(self):
        pass

    @classmethod
    def create_staff_member_(cls, user, service):
        staff_member = StaffMember.objects.create(user=user)
        staff_member.services_offered.add(service)
        return staff_member


class AppointmentRequestMixin:
    def __init__(self):
        pass

    @classmethod
    def create_appointment_request_(cls, service, staff_member, date_=date.today(), start_time=time(9, 0),
                                    end_time=time(10, 0)):
        return AppointmentRequest.objects.create(
                date=date_,
                start_time=start_time,
                end_time=end_time,
                service=service,
                staff_member=staff_member
        )

    @classmethod
    def clean_appt_request_for_user_(cls, user):
        AppointmentRequest.objects.filter(staff_member__user=user).delete()


class AppointmentMixin:
    def __init__(self):
        pass

    @classmethod
    def create_appointment_(cls, user, appointment_request, phone="+12392340543",
                            address="Stargate Command, Cheyenne Mountain Complex, Colorado Springs, CO"):
        return Appointment.objects.create(
                client=user,
                appointment_request=appointment_request,
                phone=phone,
                address=address
        )

    @classmethod
    def clean_appointment_for_user_(cls, user):
        Appointment.objects.filter(client=user).delete()


class AppointmentRescheduleHistoryMixin:
    def __init__(self):
        pass

    @classmethod
    def create_reschedule_history_(cls, appointment_request, date_, start_time, end_time, staff_member,
                                   reason_for_rescheduling="Zat'nik'tel Discharge"):
        return AppointmentRescheduleHistory.objects.create(
                appointment_request=appointment_request,
                date=date_,
                start_time=start_time,
                end_time=end_time,
                staff_member=staff_member,
                reason_for_rescheduling=reason_for_rescheduling
        )


class ConfigMixin:
    def __init__(self):
        pass

    @classmethod
    def create_config_(cls, lead_time=time(9, 0), finish_time=time(17, 0), slot_duration=30,
                       appointment_buffer_time=0):
        return Config.objects.create(
                lead_time=lead_time,
                finish_time=finish_time,
                slot_duration=slot_duration,
                appointment_buffer_time=appointment_buffer_time
        )
