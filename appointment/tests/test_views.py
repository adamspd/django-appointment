# test_views.py
# Path: appointment/tests/test_views.py

import datetime
import json
import uuid
from datetime import date, time, timedelta
from unittest.mock import MagicMock, patch

from django.contrib import messages
from django.contrib.messages import get_messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpResponseRedirect
from django.test import Client
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext as _

from appointment.messages_ import passwd_error
from appointment.models import (
    Appointment, AppointmentRequest, AppointmentRescheduleHistory, Config, DayOff, EmailVerificationCode,
    PasswordResetToken, StaffMember
)
from appointment.tests.base.base_test import BaseTest
from appointment.utils.db_helpers import Service, WorkingHours, create_user_with_username
from appointment.utils.error_codes import ErrorCode
from appointment.views import (
    create_appointment, get_appointment_data_from_post_request, get_client_data_from_post,
    redirect_to_payment_or_thank_you_page, verify_user_and_login
)


class ViewsTestCase(BaseTest):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.factory = RequestFactory()
        self.staff_member = self.staff_member1
        WorkingHours.objects.create(staff_member=self.staff_member1, day_of_week=0,
                                    start_time=datetime.time(8, 0), end_time=datetime.time(12, 0))
        WorkingHours.objects.create(staff_member=self.staff_member1, day_of_week=2,
                                    start_time=datetime.time(8, 0), end_time=datetime.time(12, 0))
        self.ar = self.create_appt_request_for_sm1()
        self.request = self.factory.get('/')
        self.user1.is_staff = True
        self.request.user = self.user1
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(self.request)
        self.request.session.save()

        middleware = MessageMiddleware(lambda req: None)
        middleware.process_request(self.request)
        self.request.session.save()
        self.appointment = self.create_appointment_for_user1()
        self.tomorrow = date.today() + timedelta(days=1)
        self.appt = self.create_appointment_for_user1()
        self.data = {
            'isCreating': False, 'service_id': '1', 'appointment_id': self.appt.id, 'client_name': 'Bryan Zap',
            'client_email': 'bz@gmail.com', 'client_phone': '+33769992738', 'client_address': 'Naples, Florida',
            'want_reminder': 'false', 'additional_info': '', 'start_time': '15:00:26',
            'date': self.tomorrow.strftime('%Y-%m-%d')
        }
        self.url_display_appt = reverse('appointment:display_appointment', args=[self.appointment.id])
        self.url_add_day_off = reverse('appointment:add_day_off', args=[self.staff_member.user_id])
        self.other_staff_member = self.staff_member2
        self.day_off = DayOff.objects.create(staff_member=self.staff_member,
                                             start_date=date.today() + timedelta(days=1),
                                             end_date=date.today() + timedelta(days=2), description="Day off")
        self.random_user = self.create_user_()

    def need_normal_login(self):
        self.client.force_login(self.random_user)

    def need_staff_login(self, user=None):
        if user is not None:
            user.is_staff = True
            user.save()
            self.client.force_login(user)
        self.user1.is_staff = True
        self.user1.save()
        self.client.force_login(self.user1)

    def need_superuser_login(self):
        self.user1.is_superuser = True
        self.user1.save()
        self.client.force_login(self.user1)

    def clean_staff_member_objects(self):
        """Delete all AppointmentRequests and Appointments linked to the StaffMember instance of self.user1."""
        AppointmentRequest.objects.filter(staff_member__user=self.user1).delete()
        Appointment.objects.filter(appointment_request__staff_member__user=self.user1).delete()

    def remove_staff_member(self):
        """Remove the StaffMember instance of self.user1."""
        self.clean_staff_member_objects()
        StaffMember.objects.filter(user=self.user1).delete()

    def test_get_available_slots_ajax(self):
        """get_available_slots_ajax view should return a JSON response with available slots for the selected date."""
        url = reverse('appointment:available_slots_ajax')
        response = self.client.get(url, {'selected_date': date.today().isoformat()},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertIn('date_chosen', response_data)
        self.assertIn('available_slots', response_data)
        self.assertFalse(response_data.get('error'))

    def test_get_available_slots_ajax_past_date(self):
        """get_available_slots_ajax view should return an error if the selected date is in the past."""
        url = reverse('appointment:available_slots_ajax')
        past_date = (date.today() - timedelta(days=1)).isoformat()
        response = self.client.get(url, {'selected_date': past_date}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['error'], True)
        self.assertEqual(response.json()['message'], 'Date is in the past')

    def test_get_next_available_date_ajax(self):
        """get_next_available_date_ajax view should return a JSON response with the next available date."""
        data = {'staff_id': self.staff_member.id}
        url = reverse('appointment:request_next_available_slot', args=[self.service1.id])
        response = self.client.get(url, data=data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertIsNotNone(response_data)
        self.assertIsNotNone(response_data['next_available_date'])

    def test_appointment_request(self):
        """Test if the appointment request form can be rendered."""
        url = reverse('appointment:appointment_request', args=[self.service1.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.service1.name, str(response.content))
        self.assertIn('all_staff_members', response.context)
        self.assertIn('service', response.context)

    def test_appointment_request_submit_valid(self):
        """Test if a valid appointment request can be submitted."""
        url = reverse('appointment:appointment_request_submit')
        post_data = {
            'date': date.today().isoformat(),
            'start_time': time(9, 0),
            'end_time': time(10, 0),
            'service': self.service1.id,
            'staff_member': self.staff_member.id,
        }
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 302)  # Redirect status
        # Check if an AppointmentRequest object was created
        self.assertTrue(AppointmentRequest.objects.filter(service=self.service1).exists())

    def test_appointment_request_submit_invalid(self):
        """Test if an invalid appointment request can be submitted."""
        url = reverse('appointment:appointment_request_submit')
        post_data = {}  # Missing required data
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)  # Rendering the form with errors
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)  # Ensure there are form errors

    def test_verify_user_and_login_valid(self):
        """Test if a user can be verified and logged in."""
        code = EmailVerificationCode.generate_code(user=self.user1)
        result = verify_user_and_login(self.request, self.user1, code)
        self.assertTrue(result)

    def test_verify_user_and_login_invalid(self):
        """Test if a user cannot be verified and logged in with an invalid code."""
        invalid_code = '000000'  # An invalid code
        result = verify_user_and_login(self.request, self.user1, invalid_code)
        self.assertFalse(result)

    def test_enter_verification_code_valid(self):
        """Test if a valid verification code can be entered."""
        code = EmailVerificationCode.generate_code(user=self.user1)
        url = reverse('appointment:enter_verification_code', args=[self.ar.id, self.ar.id_request])
        post_data = {'code': code}  # Assuming a valid code for the test setup
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)

    def test_enter_verification_code_invalid(self):
        """Test if an invalid verification code can be entered."""
        url = reverse('appointment:enter_verification_code', args=[self.ar.id, self.ar.id_request])
        post_data = {'code': '000000'}  # Invalid code
        response = self.client.post(url, post_data)
        self.assertEqual(response.status_code, 200)  # Stay on the same page
        # Check for an error message
        messages_list = list(messages.get_messages(response.wsgi_request))
        self.assertIn(_("Invalid verification code."), [str(msg) for msg in messages_list])

    def test_default_thank_you(self):
        """Test if the default thank you page can be rendered."""
        appointment = Appointment.objects.create(client=self.user1, appointment_request=self.ar)
        url = reverse('appointment:default_thank_you', args=[appointment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(appointment.get_service_name(), str(response.content))

    def test_staff_user_without_staff_member_instance(self):
        """Test that a staff user without a staff member instance receives an appropriate error message."""
        self.clean_staff_member_objects()

        # Now safely delete the StaffMember instance
        StaffMember.objects.filter(user=self.user1).delete()

        self.user1.save()  # Save the user to the database after updating
        self.need_staff_login()

        url = reverse('appointment:get_user_appointments')
        response = self.client.get(url)

        message_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any(
            message.message == "User doesn't have a staff member instance. Please contact the administrator." for
            message in message_list),
            "Expected error message not found in messages.")

    def test_delete_appointment(self):
        self.need_staff_login()

        url = reverse('appointment:delete_appointment', args=[self.appointment.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)  # Redirect status code
        self.assertRedirects(response, reverse('appointment:get_user_appointments'))

        # Check for success messages
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any(_("Appointment deleted successfully!") in str(message) for message in messages_list))

        # Check if appointment is deleted
        appointment_exists = Appointment.objects.filter(pk=self.appointment.id).exists()
        self.assertFalse(appointment_exists, "Appointment should be deleted but still exists.")

    def test_delete_appointment_ajax(self):
        self.need_staff_login()

        url = reverse('appointment:delete_appointment_ajax')
        data = json.dumps({'appointment_id': self.appointment.id})
        response = self.client.post(url, data, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        # Expecting both 'message' and 'success' in the response
        expected_response = {"message": "Appointment deleted successfully.", "success": True}
        self.assertEqual(json.loads(response.content), expected_response)

        # Check if appointment is deleted
        appointment_exists = Appointment.objects.filter(pk=self.appointment.id).exists()
        self.assertFalse(appointment_exists, "Appointment should be deleted but still exists.")

    def test_delete_appointment_without_permission(self):
        """Test that deleting an appointment without permission fails."""
        self.need_staff_login()  # Login as a regular staff user

        # Try to delete an appointment belonging to a different staff member
        different_appointment = self.create_appointment_for_user2()
        url = reverse('appointment:delete_appointment', args=[different_appointment.id])

        response = self.client.post(url)

        # Check that the user is redirected due to lack of permissions
        self.assertEqual(response.status_code, 403)

        # Verify that the appointment still exists in the database
        self.assertTrue(Appointment.objects.filter(id=different_appointment.id).exists())

    def test_delete_appointment_ajax_without_permission(self):
        """Test that deleting an appointment via AJAX without permission fails."""
        self.need_staff_login()  # Login as a regular staff user

        # Try to delete an appointment belonging to a different staff member
        different_appointment = self.create_appointment_for_user2()
        url = reverse('appointment:delete_appointment_ajax')

        response = self.client.post(url, {'appointment_id': different_appointment.id}, content_type='application/json')

        # Check that the response indicates failure due to lack of permissions
        self.assertEqual(response.status_code, 403)
        response_data = response.json()
        self.assertEqual(response_data['message'], _("You can only delete your own appointments."))
        self.assertFalse(response_data['success'])

        # Verify that the appointment still exists in the database
        self.assertTrue(Appointment.objects.filter(id=different_appointment.id).exists())

    def test_remove_staff_member(self):
        self.need_superuser_login()
        self.clean_staff_member_objects()

        url = reverse('appointment:remove_staff_member', args=[self.staff_member.user_id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)  # Redirect status code
        self.assertRedirects(response, reverse('appointment:user_profile'))

        # Check for success messages
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any(_("Staff member deleted successfully!") in str(message) for message in messages_list))

        # Check if staff member is deleted
        staff_member_exists = StaffMember.objects.filter(pk=self.staff_member.id).exists()
        self.assertFalse(staff_member_exists, "Appointment should be deleted but still exists.")

    def test_fetch_service_list_for_staff(self):
        self.need_staff_login()

        # Assuming self.service1 and self.service2 are services linked to self.staff_member1
        self.staff_member1.services_offered.add(self.service1, self.service2)
        staff_member_services = [self.service1, self.service2]

        # Simulate a request without appointmentId
        url = reverse('appointment:fetch_service_list_for_staff')
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertEqual(response_data["message"], "Successfully fetched services.")
        self.assertCountEqual(
            response_data["services_offered"],
            [{"id": service.id, "name": service.name} for service in staff_member_services]
        )

        # Create a test appointment and link it to self.staff_member1
        test_appointment = self.create_appointment_for_user1()

        # Simulate a request with appointmentId
        url_with_appointment = f"{url}?appointmentId={test_appointment.id}"
        response_with_appointment = self.client.get(url_with_appointment, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response_with_appointment.status_code, 200)
        response_data_with_appointment = response_with_appointment.json()
        self.assertEqual(response_data_with_appointment["message"], "Successfully fetched services.")
        # Assuming the staff member linked to the appointment offers the same services
        self.assertCountEqual(
            response_data_with_appointment["services_offered"],
            [{"id": service.id, "name": service.name} for service in staff_member_services]
        )

    def test_fetch_service_list_for_staff_no_staff_member_instance(self):
        """Test that a superuser without a StaffMember instance receives an appropriate error message."""
        self.need_superuser_login()

        # Ensure the superuser does not have a StaffMember instance
        StaffMember.objects.filter(user=self.user1).delete()

        url = reverse('appointment:fetch_service_list_for_staff')
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check the response status code and content
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('message', response_data)
        self.assertEqual(response_data['message'], _("You're not a staff member. Can't perform this action !"))
        self.assertFalse(response_data['success'])

    def test_fetch_service_list_for_staff_no_services_offered(self):
        """Test fetching services for a staff member who offers no services."""
        self.need_staff_login()

        # Assuming self.staff_member1 offers no services
        self.staff_member1.services_offered.clear()

        url = reverse('appointment:fetch_service_list_for_staff')
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check response status code and content
        self.assertEqual(response.status_code, 404)
        response_data = response.json()
        self.assertIn('message', response_data)
        self.assertEqual(response_data['message'], _("No services offered by this staff member."))
        self.assertFalse(response_data['success'])

    def test_update_appt_min_info_create(self):
        self.need_staff_login()

        # Preparing data
        self.data.update({'isCreating': True, 'appointment_id': None})
        url = reverse('appointment:update_appt_min_info')

        # Making the request
        response = self.client.post(url, data=json.dumps(self.data), content_type='application/json',
                                    **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})

        # Check response status
        self.assertEqual(response.status_code, 200)

        # Check response content
        response_data = response.json()
        self.assertIn('message', response_data)
        self.assertEqual(response_data['message'], 'Appointment created successfully.')
        self.assertIn('appt', response_data)

        # Verify appointment created in the database
        appointment_id = response_data['appt'][0]['id']
        self.assertTrue(Appointment.objects.filter(id=appointment_id).exists())

    def test_update_appt_min_info_update(self):
        self.need_superuser_login()

        # Create an appointment to update
        url = reverse('appointment:update_appt_min_info')

        # Making the request
        response = self.client.post(url, data=json.dumps(self.data), content_type='application/json',
                                    **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})

        # Check response status
        self.assertEqual(response.status_code, 200)

        # Check response content
        response_data = response.json()
        self.assertIn('message', response_data)
        self.assertEqual(response_data['message'], 'Appointment updated successfully.')
        self.assertIn('appt', response_data)

        # Verify appointment updated in the database
        updated_appt = Appointment.objects.get(id=self.appt.id)
        self.assertEqual(updated_appt.client.email, self.data['client_email'])

    def test_update_nonexistent_appointment(self):
        self.need_superuser_login()

        # Preparing data with a non-existent appointment ID
        self.data['appointment_id'] = 999
        url = reverse('appointment:update_appt_min_info')

        # Making the request
        response = self.client.post(url, data=json.dumps(self.data), content_type='application/json',
                                    **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})

        # Check response status and content
        self.assertEqual(response.status_code, 404)
        response_data = response.json()
        self.assertIn('message', response_data)
        self.assertEqual(response_data['message'], "Appointment does not exist.")

    def test_update_with_nonexistent_service(self):
        self.need_superuser_login()

        # Preparing data with a non-existent service ID
        self.data['service_id'] = 999
        url = reverse('appointment:update_appt_min_info')

        # Making the request
        response = self.client.post(url, data=json.dumps(self.data), content_type='application/json',
                                    **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})

        # Check response status and content
        self.assertEqual(response.status_code, 404)
        response_data = response.json()
        self.assertIn('message', response_data)
        self.assertEqual(response_data['message'], "Service does not exist.")

    def test_update_with_invalid_data_causing_exception(self):
        self.need_superuser_login()

        # Preparing invalid data to trigger an exception, for example here, no email address
        data = {
            'isCreating': False, 'service_id': '1', 'appointment_id': self.appt.id,
        }
        url = reverse('appointment:update_appt_min_info')

        # Making the request
        response = self.client.post(url, data=json.dumps(data), content_type='application/json',
                                    **{'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})

        # Check response status and content
        self.assertEqual(response.status_code, 400)
        response_data = response.json()
        self.assertIn('message', response_data)

    def test_delete_service_with_superuser(self):
        self.need_superuser_login()
        # Test deletion with a superuser
        response = self.client.get(reverse('appointment:delete_service', args=[self.service1.id]))

        # Check if the service was deleted
        self.assertFalse(Service.objects.filter(id=self.service1.id).exists())

        # Check if the success message is added
        messages_ = list(get_messages(response.wsgi_request))
        self.assertIn(_("Service deleted successfully!"), [m.message for m in messages_])

        # Check if it redirects to the user profile
        self.assertRedirects(response, reverse('appointment:user_profile'))

    def test_delete_service_without_superuser(self):
        # Log in as a regular/staff user
        self.need_staff_login()

        response = self.client.get(reverse('appointment:delete_service', args=[self.service1.id]))

        # Check for a forbidden status code, as only superusers should be able to delete services
        self.assertEqual(response.status_code, 403)

    def test_delete_nonexistent_service(self):
        self.need_superuser_login()
        # Try to delete a service that does not exist
        response = self.client.get(reverse('appointment:delete_service', args=[99999]))

        # Check for a 404-status code
        self.assertEqual(response.status_code, 404)

    def test_remove_staff_member_with_superuser(self):
        self.need_superuser_login()
        self.clean_staff_member_objects()
        # Test removal of staff member by a superuser
        response = self.client.get(reverse('appointment:remove_superuser_staff_member'))

        # Check if the StaffMember instance was deleted
        self.assertFalse(StaffMember.objects.filter(user=self.user1).exists())

        # Check if it redirects to the user profile
        self.assertRedirects(response, reverse('appointment:user_profile'))

    def test_remove_staff_member_without_superuser(self):
        # Log out superuser and log in as a regular user
        self.need_staff_login()
        response = self.client.get(reverse('appointment:remove_superuser_staff_member'))

        # Check for a forbidden status code, as only superusers should be able to remove staff members
        self.assertEqual(response.status_code, 403)

    def test_make_staff_member_with_superuser(self):
        self.need_superuser_login()
        self.remove_staff_member()
        # Test creating a staff member by a superuser
        response = self.client.get(reverse('appointment:make_superuser_staff_member'))

        # Check if the StaffMember instance was created
        self.assertTrue(StaffMember.objects.filter(user=self.user1).exists())

        # Check if it redirects to the user profile
        self.assertRedirects(response, reverse('appointment:user_profile'))

    def test_make_staff_member_without_superuser(self):
        self.need_staff_login()
        response = self.client.get(reverse('appointment:make_superuser_staff_member'))

        # Check for a forbidden status code, as only superusers should be able to create staff members
        self.assertEqual(response.status_code, 403)

    def test_is_user_staff_admin_with_staff_member(self):
        """Test that a user with a StaffMember instance is identified as a staff admin."""
        self.need_staff_login()

        # Ensure the user has a StaffMember instance
        if not StaffMember.objects.filter(user=self.user1).exists():
            StaffMember.objects.create(user=self.user1)

        url = reverse('appointment:is_user_staff_admin')
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check the response status code and content
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('message', response_data)
        self.assertEqual(response_data['message'], _("User is a staff member."))

    def test_is_user_staff_admin_without_staff_member(self):
        """Test that a user without a StaffMember instance is not identified as a staff admin."""
        self.need_staff_login()

        # Ensure the user does not have a StaffMember instance
        StaffMember.objects.filter(user=self.user1).delete()

        url = reverse('appointment:is_user_staff_admin')
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        # Check the response status code and content
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertIn('message', response_data)
        self.assertEqual(response_data['message'], _("User is not a staff member."))

    def test_display_appointment_authenticated_staff_user(self):
        # Log in as staff user
        self.need_staff_login()
        response = self.client.get(self.url_display_appt)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'administration/display_appointment.html')

    def test_display_appointment_authenticated_superuser(self):
        # Log in as superuser
        self.need_superuser_login()
        response = self.client.get(self.url_display_appt)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'administration/display_appointment.html')

    def test_display_appointment_unauthenticated_user(self):
        # Attempt access without logging in
        response = self.client.get(self.url_display_appt)
        self.assertNotEqual(response.status_code, 200)  # Expect redirection or error

    def test_display_appointment_authenticated_unauthorized_user(self):
        # Log in as a regular user
        self.need_normal_login()
        response = self.client.get(self.url_display_appt)
        self.assertNotEqual(response.status_code, 200)  # Expect redirection or error

    def test_display_appointment_non_existent(self):
        # Log in as staff user
        self.need_superuser_login()
        non_existent_url = reverse('appointment:display_appointment', args=[99999])  # Non-existent appointment ID
        response = self.client.get(non_existent_url)
        self.assertEqual(response.status_code, 404)  # Expect 404 error

    def test_add_day_off_authenticated_staff_user(self):
        # Log in as staff user
        self.need_staff_login()
        response = self.client.post(self.url_add_day_off, data={'start_date': '2050-01-01', 'end_date': '2050-01-01',
                                                                'description': 'Test reason'})
        self.assertEqual(response.status_code, 200)  # Assuming success redirects or shows a success message

    def test_add_day_off_authenticated_superuser_for_other(self):
        # Log in as superuser
        self.need_superuser_login()
        other_staff_user_id = self.other_staff_member.user.pk
        response = self.client.post(reverse('appointment:add_day_off', args=[other_staff_user_id]),
                                    data={'start_date': '2023-01-02', 'end_date': '2050-01-01',
                                          'description': 'Admin adding for staff'})
        self.assertEqual(response.status_code, 200)  # Assuming superuser can add for others

    def test_add_day_off_unauthenticated_user(self):
        # Attempt access without logging in
        response = self.client.post(self.url_add_day_off, data={'start_date': '2050-01-01', 'end_date': '2050-01-01',
                                                                'description': 'Test reason'})
        self.assertNotEqual(response.status_code, 200)  # Expect redirection or error

    def test_add_day_off_authenticated_unauthorized_user(self):
        # Log in as a regular user
        self.need_normal_login()
        unauthorized_staff_user_id = self.other_staff_member.user.pk
        response = self.client.post(reverse('appointment:add_day_off', args=[unauthorized_staff_user_id]),
                                    data={'start_date': '2050-01-01', 'end_date': '2050-01-01',
                                          'description': 'Trying to add for others'})
        self.assertNotEqual(response.status_code, 200)  # Expect redirection or error due to unauthorized action

    def test_update_day_off_authenticated_staff_user(self):
        # Log in as staff user who owns the day off
        self.need_staff_login()
        url = reverse('appointment:update_day_off', args=[self.day_off.id])
        response = self.client.post(url, {'start_date': '2050-01-01', 'end_date': '2050-01-01',
                                          'description': 'Updated reason'})
        self.assertEqual(response.status_code, 200)

    def test_update_day_off_unauthorized_user(self):
        # Log in as another staff user
        self.need_normal_login()
        url = reverse('appointment:update_day_off', args=[self.day_off.id])
        response = self.client.post(url, {'start_date': '2050-01-01', 'end_date': '2050-01-01',
                                          'description': 'Trying unauthorized update'}, 'json')
        self.assertEqual(response.status_code, 403)  # Expect forbidden error

    def test_update_nonexistent_day_off(self):
        self.need_staff_login()
        non_existent_day_off_id = 99999
        url = reverse('appointment:update_day_off', args=[non_existent_day_off_id])
        response = self.client.post(url, data={'start_date': '2050-01-01', 'end_date': '2050-01-01',
                                               'description': 'Non existent day off'})
        self.assertEqual(response.status_code, 404)  # Expect 404 error

    def test_delete_day_off_authenticated_super_user(self):
        # Log in as staff user
        self.need_superuser_login()
        url = reverse('appointment:delete_day_off', args=[self.day_off.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Assuming success redirects to the user profile

    def test_delete_day_off_unauthorized_user(self):
        # Log in as another staff user
        self.need_normal_login()
        url = reverse('appointment:delete_day_off', args=[self.day_off.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)  # Expect access denied

    def test_delete_nonexistent_day_off(self):
        self.need_staff_login()
        non_existent_day_off_id = 99999
        url = reverse('appointment:delete_day_off', args=[non_existent_day_off_id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class SetPasswordViewTests(BaseTest):
    def setUp(self):
        super().setUp()
        user_data = {
            'username': 'test_user', 'email': 'test@example.com', 'password': 'oldpassword', 'first_name': 'John',
            'last_name': 'Doe'
        }
        self.user = create_user_with_username(user_data)
        self.token = PasswordResetToken.create_token(user=self.user, expiration_minutes=2880)  # 2 days expiration
        self.ui_db64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.relative_set_passwd_link = reverse('appointment:set_passwd', args=[self.ui_db64, self.token.token])
        self.valid_link = reverse('appointment:set_passwd', args=[self.ui_db64, str(self.token.token)])

    def test_get_request_with_valid_token(self):
        assert PasswordResetToken.objects.filter(user=self.user, token=self.token.token).exists(), ("Token not found "
                                                                                                    "in database")
        response = self.client.get(self.valid_link)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "form")
        self.assertNotContains(response, "The password reset link is invalid or has expired.")

    def test_post_request_with_valid_token_and_correct_password(self):
        new_password_data = {'new_password1': 'newstrongpassword123', 'new_password2': 'newstrongpassword123'}
        response = self.client.post(self.valid_link, new_password_data)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(new_password_data['new_password1']))
        messages_ = list(get_messages(response.wsgi_request))
        self.assertTrue(any(msg.message == _("Password reset successfully.") for msg in messages_))

    def test_get_request_with_expired_token(self):
        expired_token = PasswordResetToken.create_token(user=self.user, expiration_minutes=-60)
        expired_token_link = reverse('appointment:set_passwd', args=[self.ui_db64, str(expired_token.token)])
        response = self.client.get(expired_token_link)
        self.assertEqual(response.status_code, 200)
        self.assertIn('messages', response.context)
        self.assertEqual(response.context['page_message'], passwd_error)

    def test_get_request_with_invalid_token(self):
        invalid_token = str(uuid.uuid4())
        invalid_token_link = reverse('appointment:set_passwd', args=[self.ui_db64, invalid_token])
        response = self.client.get(invalid_token_link, follow=True)
        self.assertEqual(response.status_code, 200)
        messages_ = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(msg.message == _("The password reset link is invalid or has expired.") for msg in messages_))

    def test_post_request_with_invalid_token(self):
        invalid_token = str(uuid.uuid4())
        invalid_token_link = reverse('appointment:set_passwd', args=[self.ui_db64, invalid_token])
        new_password = 'newpassword123'
        post_data = {'new_password1': new_password, 'new_password2': new_password}
        response = self.client.post(invalid_token_link, post_data)
        self.user.refresh_from_db()
        self.assertFalse(self.user.check_password(new_password))
        messages_ = list(get_messages(response.wsgi_request))
        self.assertTrue(any(_("The password reset link is invalid or has expired.") in str(m) for m in messages_))

    def test_post_request_with_expired_token(self):
        expired_token = PasswordResetToken.create_token(user=self.user, expiration_minutes=-60)
        expired_token_link = reverse('appointment:set_passwd', args=[self.ui_db64, str(expired_token.token)])
        new_password_data = {'new_password1': 'newpassword', 'new_password2': 'newpassword'}
        response = self.client.post(expired_token_link, new_password_data)
        self.assertEqual(response.status_code, 200)
        messages_ = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(msg.message == _("The password reset link is invalid or has expired.") for msg in messages_))


class GetNonWorkingDaysAjaxTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.url = reverse('appointment:get_non_working_days_ajax')

    def test_no_staff_member_selected(self):
        """Test the response when no staff member is selected."""
        response = self.client.get(self.url, {'staff_id': 'none'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['message'], _('No staff member selected'))
        self.assertIn('errorCode', response_data)
        self.assertEqual(response_data['errorCode'], ErrorCode.STAFF_ID_REQUIRED.value)

    def test_valid_staff_member_selected(self):
        """Test the response for a valid staff member selection."""
        response = self.client.get(self.url, {'staff_id': self.staff_member1.id},
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        response_data = response.json()
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['message'], _('Successfully retrieved non-working days'))
        self.assertIn('non_working_days', response_data)
        self.assertTrue(isinstance(response_data['non_working_days'], list))

    def test_ajax_required(self):
        """Ensure the view only responds to AJAX requests."""
        non_ajax_response = self.client.get(self.url, {'staff_id': self.staff_member1.id})
        self.assertEqual(non_ajax_response.status_code, 200)


class AppointmentClientInformationTest(BaseTest):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.ar = self.create_appt_request_for_sm1()
        self.url = reverse('appointment:appointment_client_information', args=[self.ar.pk, self.ar.id_request])
        self.factory = RequestFactory()
        self.request = self.factory.get('/')
        self.valid_form_data = {
            'name': 'Test Client',
            'service_id': '1',
            'payment_type': 'full',
            'email': 'testuser@example.com',
            'phone': '+1234567890',
            'address': '123 Test St.',
        }

    def test_get_request(self):
        """Test the view with a GET request."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'appointment/appointment_client_information.html')

    def test_post_request_invalid_form(self):
        """Test the view with an invalid POST request."""
        response = self.client.post(self.url, {})  # Empty data for invalid form
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'appointment/appointment_client_information.html')

    def test_already_submitted_session(self):
        """Test the view when the appointment has already been submitted."""
        session = self.client.session
        session[f'appointment_submitted_{self.ar.id_request}'] = True
        session.save()

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'error_pages/304_already_submitted.html')


class PrepareRescheduleAppointmentViewTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.ar = self.create_appt_request_for_sm1()
        self.url = reverse('appointment:prepare_reschedule_appointment', args=[self.ar.id_request])

    @patch('appointment.utils.db_helpers.can_appointment_be_rescheduled', return_value=True)
    def test_reschedule_appointment_allowed(self, mock_can_appointment_be_rescheduled):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('all_staff_members', response.context)
        self.assertIn('available_slots', response.context)
        self.assertIn('service', response.context)
        self.assertIn('staff_member', response.context)

    def test_reschedule_appointment_not_allowed(self):
        self.service1.reschedule_limit = 0
        self.service1.allow_rescheduling = True
        self.service1.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, 'error_pages/403_forbidden_rescheduling.html')

    def test_reschedule_appointment_context_data(self):
        Config.objects.create(app_offered_by_label="Test Label")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['label'], "Test Label")
        self.assertEqual(response.context['page_title'], f"Rescheduling appointment for {self.service1.name}")
        self.assertTrue('date_chosen' in response.context)
        self.assertTrue('page_description' in response.context)
        self.assertTrue('timezoneTxt' in response.context)


class RescheduleAppointmentSubmitViewTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.ar = self.create_appt_request_for_sm1(date_=timezone.now().date() + datetime.timedelta(days=1))
        self.appointment = self.create_appointment_for_user1(appointment_request=self.ar)
        self.url = reverse('appointment:reschedule_appointment_submit')
        self.post_data = {
            'appointment_request_id': self.ar.id_request,
            'date': (timezone.now().date() + datetime.timedelta(days=2)).isoformat(),
            'start_time': '10:00',
            'end_time': '11:00',
            'staff_member': self.staff_member1.id,
            'reason_for_rescheduling': 'Need a different time',
        }

    def test_post_request_with_valid_form(self):
        with patch('appointment.views.AppointmentRequestForm.is_valid', return_value=True), \
                patch('appointment.views.send_reschedule_confirmation_email') as mock_send_email:
            response = self.client.post(self.url, self.post_data)
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, 'appointment/rescheduling_thank_you.html')
            mock_send_email.assert_called_once()
            self.assertTrue(AppointmentRescheduleHistory.objects.exists())

    def test_post_request_with_invalid_form(self):
        # Simulate an invalid form submission
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, 404)

    def test_get_request(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'appointment/appointments.html')

    def test_reschedule_not_allowed(self):
        # Simulate the scenario where rescheduling is not allowed by setting the reschedule limit to 0
        self.service1.reschedule_limit = 0
        self.service1.allow_rescheduling = False
        self.service1.save()

        response = self.client.post(self.url, self.post_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'appointment/appointments.html')
        messages_list = list(get_messages(response.wsgi_request))
        self.assertTrue(any(
            _("There was an error in your submission. Please check the form and try again.") in str(message) for message
            in messages_list))


class ConfirmRescheduleViewTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.client = Client()
        self.ar = self.create_appt_request_for_sm1()
        self.create_appointment_for_user1(appointment_request=self.ar)
        self.reschedule_history = AppointmentRescheduleHistory.objects.create(
            appointment_request=self.ar,
            date=timezone.now().date() + timezone.timedelta(days=2),
            start_time='10:00',
            end_time='11:00',
            staff_member=self.staff_member1,
            id_request='unique_id_request',
            reschedule_status='pending'
        )
        self.url = reverse('appointment:confirm_reschedule', args=[self.reschedule_history.id_request])

    def test_confirm_reschedule_valid(self):
        response = self.client.get(self.url)
        self.reschedule_history.refresh_from_db()
        self.ar.refresh_from_db()
        self.assertEqual(self.reschedule_history.reschedule_status, 'confirmed')
        self.assertEqual(response.status_code, 302)  # Redirect to thank you page
        self.assertRedirects(response, reverse('appointment:default_thank_you', args=[self.ar.appointment.id]))

    def test_confirm_reschedule_invalid_status(self):
        self.reschedule_history.reschedule_status = 'confirmed'
        self.reschedule_history.save()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)  # Render 404_not_found with error message

    def test_confirm_reschedule_no_longer_valid(self):
        with patch('appointment.models.AppointmentRescheduleHistory.still_valid', return_value=False):
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 404)  # Render 404_not_found with error message

    def test_confirm_reschedule_updates(self):
        """Ensure that the appointment request and reschedule history are updated correctly."""
        self.client.get(self.url)
        self.ar.refresh_from_db()
        self.reschedule_history.refresh_from_db()
        self.assertEqual(self.ar.staff_member, self.reschedule_history.staff_member)
        self.assertEqual(self.reschedule_history.reschedule_status, 'confirmed')

    @patch('appointment.views.notify_admin_about_reschedule')
    def test_notify_admin_about_reschedule_called(self, mock_notify_admin):
        self.client.get(self.url)
        mock_notify_admin.assert_called_once()
        self.assertTrue(mock_notify_admin.called)


class GetAppointmentDataFromPostRequestTests(BaseTest):
    def setUp(self):
        self.factory = RequestFactory()
        self.post_data = {
            'phone': '1234567890',
            'want_reminder': 'on',
            'address': '123 Test St, Test City',
            'additional_info': 'Please ring the bell.'
        }

    def test_get_appointment_data_from_post_request_with_data(self):
        """Test retrieving appointment data from a POST request with all data provided."""
        request = self.factory.post('/fake-url/', self.post_data)

        appointment_data = get_appointment_data_from_post_request(request)

        self.assertEqual(appointment_data['phone'], self.post_data['phone'])
        self.assertTrue(appointment_data['want_reminder'])
        self.assertEqual(appointment_data['address'], self.post_data['address'])
        self.assertEqual(appointment_data['additional_info'], self.post_data['additional_info'])

    def test_get_appointment_data_from_post_request_partial_data(self):
        """Test retrieving appointment data from a POST request with partial data provided."""
        partial_post_data = {
            'phone': '1234567890',
            # 'want_reminder' omitted to simulate unchecked checkbox
            'address': '123 Test St, Test City',
            # 'additional_info' omitted to simulate empty field
        }
        request = self.factory.post('/fake-url/', partial_post_data)

        appointment_data = get_appointment_data_from_post_request(request)

        self.assertEqual(appointment_data['phone'], partial_post_data['phone'])
        self.assertFalse(appointment_data['want_reminder'], "want_reminder should be False if not 'on'")
        self.assertEqual(appointment_data['address'], partial_post_data['address'])
        self.assertEqual(appointment_data['additional_info'], None, "additional_info should be None if not provided")

    def test_get_appointment_data_from_post_request_missing_data(self):
        """Test retrieving appointment data from a POST request with missing data."""
        missing_data_post = {}
        request = self.factory.post('/fake-url/', missing_data_post)

        appointment_data = get_appointment_data_from_post_request(request)

        self.assertEqual(appointment_data['phone'], None, "phone should be None if not provided")
        self.assertFalse(appointment_data['want_reminder'], "want_reminder should be False if not provided")
        self.assertEqual(appointment_data['address'], None, "address should be None if not provided")
        self.assertEqual(appointment_data['additional_info'], None, "additional_info should be None if not provided")


class GetClientDataFromPostTests(BaseTest):
    def setUp(self):
        self.factory = RequestFactory()

    def test_get_client_data_with_full_data(self):
        """Test retrieving client data from a POST request with all fields provided."""
        post_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
        }
        request = self.factory.post('/fake-url/', post_data)

        client_data = get_client_data_from_post(request)

        self.assertEqual(client_data['name'], post_data['name'])
        self.assertEqual(client_data['email'], post_data['email'])

    def test_get_client_data_with_missing_name(self):
        """Test retrieving client data from a POST request with the name missing."""
        post_data = {
            # 'name' is missing
            'email': 'john.doe@example.com',
        }
        request = self.factory.post('/fake-url/', post_data)

        client_data = get_client_data_from_post(request)

        self.assertIsNone(client_data['name'], "name should be None if not provided")
        self.assertEqual(client_data['email'], post_data['email'])

    def test_get_client_data_with_missing_email(self):
        """Test retrieving client data from a POST request with the email missing."""
        post_data = {
            'name': 'John Doe',
            # 'email' is missing
        }
        request = self.factory.post('/fake-url/', post_data)

        client_data = get_client_data_from_post(request)

        self.assertEqual(client_data['name'], post_data['name'])
        self.assertIsNone(client_data['email'], "email should be None if not provided")

    def test_get_client_data_with_empty_fields(self):
        """Test retrieving client data from a POST request with empty fields."""
        post_data = {
            'name': '',
            'email': '',
        }
        request = self.factory.post('/fake-url/', post_data)

        client_data = get_client_data_from_post(request)

        self.assertEqual(client_data['name'], '', "name should be empty string if provided as such")
        self.assertEqual(client_data['email'], '', "email should be empty string if provided as such")


class RedirectToPaymentOrThankYouPageTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.appointment = self.create_appointment_for_user1()

    @patch('appointment.views.APPOINTMENT_PAYMENT_URL', 'http://example.com/payment/')
    @patch('appointment.views.create_payment_info_and_get_url')
    def test_redirect_to_payment_page(self, mock_create_payment_info_and_get_url):
        """Test redirection to the payment page when APPOINTMENT_PAYMENT_URL is set."""
        mock_create_payment_info_and_get_url.return_value = 'http://example.com/payment/12345'
        response = redirect_to_payment_or_thank_you_page(self.appointment)

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertEqual(response.url, 'http://example.com/payment/12345')

    @patch('appointment.views.APPOINTMENT_PAYMENT_URL', '')
    @patch('appointment.views.APPOINTMENT_THANK_YOU_URL', 'appointment:default_thank_you')
    def test_redirect_to_custom_thank_you_page(self):
        """Test redirection to a custom thank-you page when APPOINTMENT_THANK_YOU_URL is set."""
        response = redirect_to_payment_or_thank_you_page(self.appointment)

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertTrue(response.url.startswith(
            reverse('appointment:default_thank_you', kwargs={'appointment_id': self.appointment.id})))

    @patch('appointment.views.APPOINTMENT_PAYMENT_URL', '')
    @patch('appointment.views.APPOINTMENT_THANK_YOU_URL', '')
    def test_redirect_to_default_thank_you_page(self):
        """Test redirection to the default thank-you page when no specific URL is set."""
        response = redirect_to_payment_or_thank_you_page(self.appointment)

        self.assertIsInstance(response, HttpResponseRedirect)
        self.assertTrue(response.url.startswith(
            reverse('appointment:default_thank_you', kwargs={'appointment_id': self.appointment.id})))


class CreateAppointmentTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.appointment_request = self.create_appt_request_for_sm1()
        self.client_data = {'name': 'John Doe', 'email': 'john@example.com'}
        self.appointment_data = {'phone': '1234567890', 'want_reminder': True, 'address': '123 Test St.',
                                 'additional_info': 'Test info'}
        self.request = RequestFactory().get('/')

    @patch('appointment.views.create_and_save_appointment')
    @patch('appointment.views.redirect_to_payment_or_thank_you_page')
    def test_create_appointment_success(self, mock_redirect, mock_create_and_save):
        """Test successful creation of an appointment and redirection."""
        # Mock the appointment creation to return an Appointment instance
        mock_appointment = MagicMock()
        mock_create_and_save.return_value = mock_appointment

        # Mock the redirection function to simulate a successful redirection
        mock_redirect.return_value = MagicMock()

        create_appointment(self.request, self.appointment_request, self.client_data, self.appointment_data)

        # Verify that create_and_save_appointment was called with the correct arguments
        mock_create_and_save.assert_called_once_with(self.appointment_request, self.client_data, self.appointment_data,
                                                     self.request)

        # Verify that the redirect_to_payment_or_thank_you_page was called with the created appointment
        mock_redirect.assert_called_once_with(mock_appointment)
