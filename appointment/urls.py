# urls.py
# Path: appointment/urls.py

"""
Author: Adams Pierre David
Since: 1.0.0
"""

from django.urls import path, include

from appointment.views import appointment_request, get_available_slots_ajax, get_next_available_date_ajax, \
    appointment_request_submit, appointment_client_information, default_thank_you, enter_verification_code, \
    get_non_working_days_ajax
from appointment.views_admin import get_user_appointments, display_appointment, user_profile, update_working_hours, \
    add_working_hours, delete_working_hours, add_day_off, update_day_off, delete_day_off, add_or_update_staff_info, \
    fetch_service_list_for_staff, update_appt_min_info, update_appt_date_time, validate_appointment_date, \
    email_change_verification_code, update_personal_info, create_new_staff_member, make_superuser_staff_member, \
    remove_superuser_staff_member, add_or_update_service, delete_service, remove_staff_member, get_service_list

app_name = 'appointment'

admin_urlpatterns = [
    # display the calendar with the events
    path('user-event/<str:response_type>/', get_user_appointments, name='get_user_event_type'),
    path('user-event/', get_user_appointments, name='get_user_appointments'),

    # create a new staff member and make/remove superuser staff member
    path('staff-member-personal-info/', create_new_staff_member, name='add_staff_member_personal_info'),
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
]

ajax_urlpatterns = [
    path('available_slots/', get_available_slots_ajax, name='available_slots_ajax'),
    path('request_next_available_slot/<int:service_id>/', get_next_available_date_ajax,
         name='request_next_available_slot'),
    path('request_staff_info/', get_non_working_days_ajax, name='get_non_working_days_ajax'),
    path('fetch_service_list_for_staff/', fetch_service_list_for_staff, name='fetch_service_list_for_staff'),
    path('update_appt_min_info/', update_appt_min_info, name="update_appt_min_info"),
    path('update_appt_date_time/', update_appt_date_time, name="update_appt_date_time"),
    path('validate_appointment_date/', validate_appointment_date, name="validate_appointment_date"),
]

urlpatterns = [
    # homepage
    path('request/<int:service_id>/', appointment_request, name='appointment_request'),
    path('request-submit/', appointment_request_submit, name='appointment_request_submit'),
    path('client-info/<int:appointment_request_id>/<str:id_request>/', appointment_client_information,
         name='appointment_client_information'),
    path('verification-code/<int:appointment_request_id>/<str:id_request>/', enter_verification_code,
         name='enter_verification_code'),
    path('verification-code/', email_change_verification_code, name='email_change_verification_code'),
    path('thank-you/<int:appointment_id>/', default_thank_you, name='default_thank_you'),
    path('ajax/', include(ajax_urlpatterns)),
    path('app-admin/', include(admin_urlpatterns)),
]
