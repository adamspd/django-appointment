# urls.py
# Path: appointment/urls.py

"""
Author: Adams Pierre David
Since: 1.0.0
"""

from django.urls import include, path

from appointment.views import (
    appointment_client_information, appointment_request, appointment_request_submit, confirm_reschedule,
    default_thank_you, enter_verification_code, get_available_slots_ajax, get_next_available_date_ajax,
    get_non_working_days_ajax, prepare_reschedule_appointment, reschedule_appointment_submit, set_passwd
)
from appointment.views_admin import (
    add_day_off, add_or_update_service, add_or_update_staff_info, add_staff_member_info, add_working_hours,
    create_new_staff_member, delete_appointment, delete_appointment_ajax, delete_day_off, delete_service,
    delete_working_hours, display_appointment, email_change_verification_code, fetch_service_list_for_staff,
    fetch_staff_list, get_service_list, get_user_appointments, is_user_staff_admin, make_superuser_staff_member,
    remove_staff_member, remove_superuser_staff_member, update_appt_date_time, update_appt_min_info, update_day_off,
    update_personal_info, update_working_hours, user_profile, validate_appointment_date
)

app_name = 'appointment'

admin_urlpatterns = [
    # display the calendar with the events
    path('appointments/<str:response_type>/', get_user_appointments, name='get_user_event_type'),
    path('appointments/', get_user_appointments, name='get_user_appointments'),

    # create a new staff member and make/remove superuser staff member
    path('add-staff-member-info/', add_staff_member_info, name='add_staff_member_info'),
    path('create-new-staff-member/', create_new_staff_member, name='add_staff_member_personal_info'),
    path('update-staff-member/<int:user_id>/', add_or_update_staff_info, name='update_staff_other_info'),
    path('add-staff-member/', add_or_update_staff_info, name='add_staff_other_info'),
    path('make-superuser-staff-member/', make_superuser_staff_member, name='make_superuser_staff_member'),
    path('remove-superuser-staff-member/', remove_superuser_staff_member, name='remove_superuser_staff_member'),

    # remove staff member
    path('remove-staff-member/<int:staff_user_id>/', remove_staff_member, name='remove_staff_member'),

    # add, update, remove services
    path('add-service/', add_or_update_service, name='add_service'),
    path('update-service/<int:service_id>/', add_or_update_service, name='update_service'),
    path('delete-service/<int:service_id>/', delete_service, name='delete_service'),
    path('service-list/', get_service_list, name='get_service_list'),
    path('service-list/<str:response_type>/', get_service_list, name='get_service_list_type'),
    path('view-service/<int:service_id>/<int:view>/', add_or_update_service, name='view_service'),

    # display details for one event
    path('display-appointment/<int:appointment_id>/', display_appointment, name='display_appointment'),

    # complete profile
    path('user-profile/<int:staff_user_id>/', user_profile, name='user_profile'),
    path('user-profile/', user_profile, name='user_profile'),
    path('update-user-info/<int:staff_user_id>/', update_personal_info, name='update_user_info'),
    path('update-user-info/', update_personal_info, name='update_user_info'),

    # add, update, delete day off with staff_user_id
    path('add-day-off/<int:staff_user_id>/', add_day_off, name='add_day_off'),
    path('update-day-off/<int:day_off_id>/<int:staff_user_id>/', update_day_off, name='update_day_off_id'),
    path('delete-day-off/<int:day_off_id>/<int:staff_user_id>/', delete_day_off, name='delete_day_off_id'),

    # add, update, delete day off without staff_user_id
    path('update-day-off/<int:day_off_id>/', update_day_off, name='update_day_off'),
    path('delete-day-off/<int:day_off_id>/', delete_day_off, name='delete_day_off'),

    # add, update, delete working hours with staff_user_id
    path('update-working-hours/<int:working_hours_id>/<int:staff_user_id>/', update_working_hours,
         name='update_working_hours_id'),
    path('add-working-hours/<int:staff_user_id>/', add_working_hours, name='add_working_hours_id'),
    path('delete-working-hours/<int:working_hours_id>/<int:staff_user_id>/', delete_working_hours,
         name='delete_working_hours_id'),

    # add, update, delete working hours without staff_user_id
    path('update-working-hours/<int:working_hours_id>/', update_working_hours, name='update_working_hours'),
    path('add-working-hours/', add_working_hours, name='add_working_hours'),
    path('delete-working-hours/<int:working_hours_id>/', delete_working_hours, name='delete_working_hours'),

    # delete appointment
    path('delete-appointment/<int:appointment_id>/', delete_appointment, name='delete_appointment'),
]

ajax_urlpatterns = [
    path('available_slots/', get_available_slots_ajax, name='available_slots_ajax'),
    path('request_next_available_slot/<int:service_id>/', get_next_available_date_ajax,
         name='request_next_available_slot'),
    path('request_staff_info/', get_non_working_days_ajax, name='get_non_working_days_ajax'),
    path('fetch_service_list_for_staff/', fetch_service_list_for_staff, name='fetch_service_list_for_staff'),
    path('fetch_staff_list/', fetch_staff_list, name='fetch_staff_list'),
    path('update_appt_min_info/', update_appt_min_info, name="update_appt_min_info"),
    path('update_appt_date_time/', update_appt_date_time, name="update_appt_date_time"),
    path('validate_appointment_date/', validate_appointment_date, name="validate_appointment_date"),
    # delete appointment ajax
    path('delete_appointment/', delete_appointment_ajax, name="delete_appointment_ajax"),
    path('is_user_staff_admin/', is_user_staff_admin, name="is_user_staff_admin"),
]

urlpatterns = [
    # homepage
    path('request/<int:service_id>/', appointment_request, name='appointment_request'),
    path('request-submit/', appointment_request_submit, name='appointment_request_submit'),
    path('appointment/<str:id_request>/reschedule/', prepare_reschedule_appointment,
         name='prepare_reschedule_appointment'),
    path('appointment-reschedule-submit/', reschedule_appointment_submit, name='reschedule_appointment_submit'),
    path('confirm-reschedule/<str:id_request>/', confirm_reschedule, name='confirm_reschedule'),
    path('client-info/<int:appointment_request_id>/<str:id_request>/', appointment_client_information,
         name='appointment_client_information'),
    path('verification-code/<int:appointment_request_id>/<str:id_request>/', enter_verification_code,
         name='enter_verification_code'),
    path('verification-code/', email_change_verification_code, name='email_change_verification_code'),
    path('thank-you/<int:appointment_id>/', default_thank_you, name='default_thank_you'),
    path('verify/<uidb64>/<str:token>/', set_passwd, name='set_passwd'),
    path('ajax/', include(ajax_urlpatterns)),
    path('app-admin/', include(admin_urlpatterns)),
]
