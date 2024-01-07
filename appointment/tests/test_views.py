import datetime
import json
from datetime import date, time, timedelta

from django.contrib import messages
from django.contrib.messages import get_messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import Client
from django.test.client import RequestFactory
from django.urls import reverse
from django.utils.translation import gettext as _

from appointment.models import Appointment, AppointmentRequest, EmailVerificationCode, StaffMember
from appointment.tests.base.base_test import BaseTest
from appointment.utils.db_helpers import Service, WorkingHours
from appointment.views import verify_user_and_login


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

    def need_staff_login(self):
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
        self.assertEqual(response.status_code, 200)
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
