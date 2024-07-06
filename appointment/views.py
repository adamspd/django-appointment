# views.py
# Path: appointment/views.py

"""
Author: Adams Pierre David
Since: 1.0.0
"""

from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import SetPasswordForm
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.timezone import get_current_timezone_name
from django.utils.translation import gettext as _
from django.views.generic import FormView, RedirectView, TemplateView, View

from appointment.forms import AppointmentForm, AppointmentRequestForm, SlotForm, ClientDataForm
from appointment.logger_config import logger
from appointment.models import (
    Appointment, AppointmentRequest, AppointmentRescheduleHistory, Config, DayOff, EmailVerificationCode,
    PasswordResetToken, Service,
    StaffMember
)
from appointment.utils.db_helpers import (
    can_appointment_be_rescheduled, check_day_off_for_staff, create_and_save_appointment, create_new_user,
    create_payment_info_and_get_url, get_non_working_days_for_staff, get_user_by_email, get_user_model,
    get_website_name, get_weekday_num_from_date, is_working_day, staff_change_allowed_on_reschedule,
    username_in_user_model
)
from appointment.utils.email_ops import notify_admin_about_appointment, notify_admin_about_reschedule, \
    send_reschedule_confirmation_email, \
    send_thank_you_email
from appointment.utils.session import get_appointment_data_from_session, handle_existing_email
from appointment.utils.view_helpers import get_locale
from .decorators import require_ajax
from .messages_ import passwd_error, passwd_set_successfully
from .services import get_appointments_and_slots, get_available_slots_for_staff
from .settings import (APPOINTMENT_PAYMENT_URL, APPOINTMENT_THANK_YOU_URL)
from .utils.date_time import convert_str_to_date
from .utils.error_codes import ErrorCode
from .utils.json_context import get_generic_context_with_extra, json_response

CLIENT_MODEL = get_user_model()


@method_decorator(require_ajax, name='dispatch')
class GetAvailableSlotsAjax(View):
    """This view handles AJAX requests to get available slots for a selected date.

    :param request: The request instance.
    :return: A JSON response containing available slots, selected date, an error flag, and an optional error message.
    """
    def get(self, request, *args, **kwargs):
        slot_form = SlotForm(request.GET)
        error_code = 0
        if not slot_form.is_valid():
            custom_data = {'error': True, 'available_slots': [], 'date_chosen': ''}
            if 'selected_date' in slot_form.errors:
                error_code = ErrorCode.PAST_DATE
            elif 'staff_member' in slot_form.errors:
                error_code = ErrorCode.STAFF_ID_REQUIRED
            message = list(slot_form.errors.as_data().items())[0][1][0].messages[0]  # dirty way to keep existing behavior
            return json_response(message=message, custom_data=custom_data, success=False,
                                 error_code=error_code)

        selected_date = slot_form.cleaned_data['selected_date']
        sm = slot_form.cleaned_data['staff_member']
        date_chosen = selected_date.strftime("%a, %B %d, %Y")
        custom_data = {'date_chosen': date_chosen}

        days_off_exist = check_day_off_for_staff(staff_member=sm, date=selected_date)
        if days_off_exist:
            message = _("Day off. Please select another date!")
            custom_data['available_slots'] = []
            return json_response(message=message, custom_data=custom_data, success=False, error_code=ErrorCode.INVALID_DATE)
        # if selected_date is not a working day for the staff, return an empty list of slots and 'message' is Day Off
        weekday_num = get_weekday_num_from_date(selected_date)
        is_working_day_ = is_working_day(staff_member=sm, day=weekday_num)

        custom_data['staff_member'] = sm.get_staff_member_name()
        if not is_working_day_:
            message = _("Not a working day for {staff_member}. Please select another date!").format(
                staff_member=sm.get_staff_member_first_name())
            custom_data['available_slots'] = []
            return json_response(message=message, custom_data=custom_data, success=False, error_code=ErrorCode.INVALID_DATE)
        available_slots = get_available_slots_for_staff(selected_date, sm)

        # Check if the selected_date is today and filter out past slots
        if selected_date == date.today():
            current_time = timezone.now().time()
            available_slots = [slot for slot in available_slots if slot.time() > current_time]

        custom_data['available_slots'] = [slot.strftime('%I:%M %p') for slot in available_slots]
        if len(available_slots) == 0:
            custom_data['error'] = True
            message = _('No availability')
            return json_response(message=message, custom_data=custom_data, success=False, error_code=ErrorCode.INVALID_DATE)
        custom_data['error'] = False
        return json_response(message='Successfully retrieved available slots', custom_data=custom_data, success=True)


get_available_slots_ajax = GetAvailableSlotsAjax.as_view()


# TODO: service id and staff id are not checked
@method_decorator(require_ajax, name='dispatch')
class GetNextAvailableDataAjaxView(View):
    """This view function handles AJAX requests to get the next available date for a service.

    :param request: The request instance.
    :param service_id: The ID of the service.
    :return: A JSON response containing the next available date.
    """
    def get(self, request, service_id, *args, **kwargs):
        staff_id = request.GET.get('staff_member')

        # If staff_id is not provided, you should handle it accordingly.
        if staff_id and staff_id != 'none':
            staff_member = get_object_or_404(StaffMember, pk=staff_id)
            service = get_object_or_404(Service, pk=service_id)

            # Fetch the days off for the staff
            days_off = DayOff.objects.filter(staff_member=staff_member).filter(
                Q(start_date__lte=date.today(), end_date__gte=date.today()) |
                Q(start_date__gte=date.today())
            )

            current_date = date.today()
            next_available_date = None
            day_offset = 0

            while next_available_date is None:
                potential_date = current_date + timedelta(days=day_offset)

                # Check if the potential date is a day off for the staff
                is_day_off = any([day_off.start_date <= potential_date <= day_off.end_date for day_off in days_off])
                # Check if the potential date is a working day for the staff
                weekday_num = get_weekday_num_from_date(potential_date)
                is_working_day_ = is_working_day(staff_member=staff_member, day=weekday_num)

                if not is_day_off and is_working_day_:
                    x, available_slots = get_appointments_and_slots(potential_date, service)
                    if available_slots:
                        next_available_date = potential_date

                day_offset += 1
            message = _('Successfully retrieved next available date')
            data = {'next_available_date': next_available_date.isoformat()}
            return json_response(message=message, custom_data=data, success=True)
        else:
            data = {'error': True}
            message = _('No staff member selected')
            return json_response(message=message, custom_data=data, success=False, error_code=ErrorCode.STAFF_ID_REQUIRED)


get_next_available_date_ajax = GetNextAvailableDataAjaxView.as_view()


def get_non_working_days_ajax(request):
    staff_id = request.GET.get('staff_member')
    error = False
    message = _('Successfully retrieved non-working days')

    if not staff_id or staff_id == 'none':
        message = _('No staff member selected')
        error_code = ErrorCode.STAFF_ID_REQUIRED
        error = True
    else:
        non_working_days = get_non_working_days_for_staff(staff_id)
        custom_data = {"non_working_days": non_working_days}
        return json_response(message=message, custom_data=custom_data, success=not error)

    custom_data = {'error': error}
    return json_response(message=message, custom_data=custom_data, success=not error, error_code=error_code)


class AppointmentRequestView(TemplateView):
    """This view handles requests to book an appointment for a service.

    :param request: The request instance.
    :param service_id: The ID of the service.
    :param staff_member_id: The ID of the staff member.
    :return: The rendered HTML page.
    """
    template_name = 'appointment/appointments.html'

    def get(self, request, service_id=None, staff_member_id=None):
        service = None
        staff_member = None
        all_staff_members = None
        available_slots = []
        config = Config.objects.first()
        label = config.app_offered_by_label if config else _("Offered by")

        if service_id:
            service = get_object_or_404(Service, pk=service_id)
            all_staff_members = StaffMember.objects.filter(services_offered=service)

            # If only one staff member for a service, choose them by default and fetch their slots.
            if all_staff_members.count() == 1:
                staff_member = all_staff_members.first()
                x, available_slots = get_appointments_and_slots(date.today(), service)

        # If a specific staff member is selected, fetch their slots.
        if staff_member_id:
            staff_member = get_object_or_404(StaffMember, pk=staff_member_id)
            y, available_slots = get_appointments_and_slots(date.today(), service)

        page_title = f"{service.name} - {get_website_name()}"
        page_description = _("Book an appointment for {s} at {wn}.").format(s=service.name, wn=get_website_name())

        date_chosen = date.today().strftime("%a, %B %d, %Y")
        extra_context = {
            'service': service,
            'staff_member': staff_member,
            'all_staff_members': all_staff_members,
            'page_title': page_title,
            'page_description': page_description,
            'available_slots': available_slots,
            'date_chosen': date_chosen,
            'locale': get_locale(),
            'timezoneTxt': get_current_timezone_name(),
            'label': label
        }
        context = get_generic_context_with_extra(request, extra_context, admin=False)
        return render(request, self.template_name, context=context)


appointment_request = AppointmentRequestView.as_view()


class AppointmentRequestSubmitView(FormView):
    """This view handles the submission of the appointment request form.

    :param request: The request instance.
    :return: The rendered HTML page.
    """
    template_name = 'appointment/appointments.html'
    form_class = AppointmentRequestForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = context['form']
        context.update(get_generic_context_with_extra(self.request, {'form': form}, admin=False))
        return context

    def form_valid(self, form):
        # Use form.cleaned_data to get the cleaned and validated data
        staff_member = form.cleaned_data['staff_member']

        staff_exists = StaffMember.objects.filter(id=staff_member.id).exists()
        if not staff_exists:
            messages.error(self.request, _("Selected staff member does not exist."))
        else:
            logger.info(
                f"date_f {form.cleaned_data['date']} start_time {form.cleaned_data['start_time']} end_time "
                f"{form.cleaned_data['end_time']} service {form.cleaned_data['service']} staff {staff_member}")
            ar = form.save()
            self.request.session[f'appointment_completed_{ar.id_request}'] = False
            # Redirect the user to the account creation page
            return redirect('appointment:appointment_client_information', appointment_request_id=ar.id,
                            id_request=ar.id_request)

    def form_invalid(self, form):
        # Handle the case if the form is not valid
        messages.error(self.request, _('There was an error in your submission. Please check the form and try again.'))
        return super().form_invalid(form)


appointment_request_submit = AppointmentRequestSubmitView.as_view()


def redirect_to_payment_or_thank_you_page(appointment):
    """This function redirects to the payment page or the thank-you page based on the configuration.

    :param appointment: The Appointment instance.
    :return: The redirect response.
    """
    if (APPOINTMENT_PAYMENT_URL is not None and APPOINTMENT_PAYMENT_URL != '') and appointment.service_is_paid():
        payment_url = create_payment_info_and_get_url(appointment)
        return HttpResponseRedirect(payment_url)
    else:
        # Determine the correct thank-you URL based on whether APPOINTMENT_THANK_YOU_URL is provided and not empty
        thank_you_url_key = 'appointment:default_thank_you'
        if APPOINTMENT_THANK_YOU_URL:
            thank_you_url_key = APPOINTMENT_THANK_YOU_URL

        thank_you_url = reverse(thank_you_url_key, kwargs={'appointment_id': appointment.id})
        return HttpResponseRedirect(thank_you_url)


def create_appointment(request, appointment_request_obj, client_data, appointment_data):
    """This function creates a new appointment and redirects to the payment page or the thank-you page.

    :param request: The request instance.
    :param appointment_request_obj: The AppointmentRequest instance.
    :param client_data: The client data.
    :param appointment_data: The appointment data.
    :return: The redirect response.
    """
    appointment = create_and_save_appointment(appointment_request_obj, client_data, appointment_data, request)
    notify_admin_about_appointment(appointment, appointment.client.first_name)
    return redirect_to_payment_or_thank_you_page(appointment)


class AppointmentClientInformationView(TemplateView):
    """This view handles client information submission for an appointment.

    :param request: The request instance.
    :param appointment_request_id: The ID of the appointment request.
    :param id_request: The unique ID of the appointment request.
    :return: The rendered HTML page.
    """
    template_name = "appointment/appointment_client_information.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        extra_context = {
            'ar': self.ar,
            'APPOINTMENT_PAYMENT_URL': APPOINTMENT_PAYMENT_URL,
            'service_name': self.ar.service.name,
        }
        context.update(get_generic_context_with_extra(self.request, extra_context, admin=False))
        return context

    def dispatch(self, request, *args, **kwargs):
        self.id_request = self.kwargs['id_request']
        self.appointment_request_id = self.kwargs['appointment_request_id']
        self.ar = get_object_or_404(AppointmentRequest, pk=self.appointment_request_id)
        if request.session.get(f'appointment_submitted_{self.id_request}', False):
            context = get_generic_context_with_extra(request, {'service_id': self.ar.service_id}, admin=False)
            return render(request, 'error_pages/304_already_submitted.html', context=context)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        kwargs.update({
            'form': AppointmentForm(),
            'client_data_form': ClientDataForm(),
        })
        response = super().get(request, *args, **kwargs)
        return response

    def create_user(self, client_data):
        return create_new_user(client_data)

    def post(self, request, *args, **kwargs):
        appointment_form = AppointmentForm(request.POST)
        client_data_form = ClientDataForm(request.POST)

        if appointment_form.is_valid() and client_data_form.is_valid():
            appointment_data = appointment_form.cleaned_data
            client_data = client_data_form.cleaned_data
            payment_type = request.POST.get('payment_type')
            self.ar.payment_type = payment_type
            self.ar.save()

            # Check if email is already in the database
            is_email_in_db = CLIENT_MODEL.objects.filter(email__exact=client_data['email']).exists()
            if is_email_in_db:
                return handle_existing_email(request, client_data, appointment_data, self.appointment_request_id, self.id_request)

            logger.info(f"Creating a new user with the given information {client_data}")
            user = self.create_new_user(client_data)
            messages.success(request, _("An account was created for you."))

            # Create a new appointment
            response = create_appointment(request, self.ar, client_data, appointment_data)
            request.session.setdefault(f'appointment_submitted_{self.id_request}', True)
            return response
        return super().get(request, *args, **kwargs)


appointment_client_information = AppointmentClientInformationView.as_view()


def verify_user_and_login(request, user, code):
    """This function verifies the user's email and logs the user in.

    :param request: The request instance.
    :param user: The User instance.
    :param code: The verification code.
    """
    if user and EmailVerificationCode.objects.filter(user=user, code=code).exists():
        logger.info(f"Email verified successfully for user {user}")
        login(request, user)
        messages.success(request, _("Email verified successfully."))
        return True
    else:
        messages.error(request, _("Invalid verification code."))
        return False


class EnterVerificationCodeView(TemplateView):
    """This view handles the submission of the email verification code.

    :param request: The request instance.
    :param appointment_request_id: The ID of the appointment request.
    :param id_request: The unique ID of the appointment request.
    :return: The rendered HTML page.
    """
    template_name = "appointment/enter_verification_code.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        extra_context = {
            'appointment_request_id': kwargs['appointment_request_id'],
            'id_request': self.kwargs['id_request'],
        }
        context.update(get_generic_context_with_extra(self.request, extra_context, admin=False))
        return context

    def post(self, request, *args, **kwargs):
        email = request.session.get('email')
        code = request.POST.get('code')
        user = get_user_by_email(email)

        if verify_user_and_login(request, user, code):
            appointment_request_object = AppointmentRequest.objects.get(pk=self.kwargs['appointment_request_id'])
            appointment_data = get_appointment_data_from_session(request)
            response = create_appointment(request=request, appointment_request_obj=appointment_request_object,
                                          client_data={'email': email}, appointment_data=appointment_data)
            appointment = Appointment.objects.get(appointment_request=appointment_request_object)
            appointment_details = {
                'Service': appointment.get_service_name(),
                'Appointment Date': appointment.get_appointment_date(),
                'Appointment Time': appointment.appointment_request.start_time,
                'Duration': appointment.get_service_duration()
            }
            send_thank_you_email(ar=appointment_request_object, user=user, email=email,
                                 appointment_details=appointment_details, request=request)
            return response
        else:
            messages.error(request, _("Invalid verification code."))
        return super().get(request, *args, **kwargs)


enter_verification_code = EnterVerificationCodeView.as_view()


class DefaultThankYouView(TemplateView):
    """This view handles the default thank you page.

    :param request: The request instance.
    :param appointment_id: The ID of the appointment.
    :return: The rendered HTML page.
    """
    template_name = "appointment/default_thank_you.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        extra_context = {
            'appointment': self.appointment,
        }
        context.update(get_generic_context_with_extra(self.request, extra_context, admin=False))
        return context

    def get(self, request, *args, **kwargs):
        self.appointment = get_object_or_404(Appointment, pk=self.kwargs['appointment_id'])
        ar = self.appointment.appointment_request
        email = self.appointment.client.email
        appointment_details = {
            _('Service'): self.appointment.get_service_name(),
            _('Appointment Date'): self.appointment.get_appointment_date(),
            _('Appointment Time'): self.appointment.appointment_request.start_time,
            _('Duration'): self.appointment.get_service_duration()
        }
        account_details = {
            _('Email address'): email,
        }
        if username_in_user_model():
            account_details[_('Username')] = self.appointment.client.username
        send_thank_you_email(ar=ar, user=self.appointment.client, email=email, appointment_details=appointment_details,
                             account_details=account_details, request=request)
        return super().get(request, *args, **kwargs)


default_thank_you = DefaultThankYouView.as_view()


class SetPasswdView(FormView):
    template_name = "appointment/set_password.html"
    form_class = SetPasswordForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        extra = {
            'page_title': _("Error"),
            'page_message': passwd_error,
            'page_description': _("Please try resetting your password again or contact support for help."),
        }
        extra_context = get_generic_context_with_extra(self.request, extra, admin=False)
        context.update(extra_context)
        return context

    def dispatch(self, request, *args, **kwargs):
        self.uidb64 = self.kwargs['uidb64']
        self.token = self.kwargs['token']
        self.uid = force_str(urlsafe_base64_decode(self.uidb64))
        self.user = get_user_model().objects.get(pk=self.uid)
        self.token_verification = PasswordResetToken.verify_token(self.user, self.token)

        if self.token_verification is None:
            messages.error(request, passwd_error)
            context = self.get_context_data()
            return render(request, 'appointment/thank_you.html', context=context)

        try:
            return super().dispatch(request, *args, **kwargs)
        except (TypeError, ValueError, OverflowError, get_user_model().DoesNotExist):
            messages.error(request, _("The password reset link is invalid or has expired."))
            context = self.get_context_data()
            return render(request, 'appointment/thank_you.html', context=context)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'user': self.user,
        })
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, _("Password reset successfully."))
        # Invalidate the token after successful password reset
        self.token_verification.mark_as_verified()
        extra = {
            'page_title': _("Password Reset Successful"),
            'page_message': passwd_set_successfully,
            'page_description': _("You can now use your new password to log in.")
        }
        context = get_generic_context_with_extra(self.request, extra, admin=False)
        return render(self.request, 'appointment/thank_you.html', context=context)


set_passwd = SetPasswdView.as_view()


class PrepareRescheduleAppointment(TemplateView):
    template_name = 'appointment/appointments.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        service = self.ar.service
        selected_sm = self.ar.staff_member
        config = Config.objects.first()
        label = config.app_offered_by_label if config else _("Offered by")
        # if staff change allowed, filter all staff offering the service otherwise, filter only the selected staff member
        staff_filter_criteria = {'id': self.ar.staff_member.id} if not staff_change_allowed_on_reschedule() else {
            'services_offered': self.ar.service}
        all_staff_members = StaffMember.objects.filter(**staff_filter_criteria)
        available_slots = get_available_slots_for_staff(self.ar.date, selected_sm)
        page_title = _("Rescheduling appointment for {s}").format(s=service.name)
        page_description = _("Reschedule your appointment for {s} at {wn}.").format(s=service.name, wn=get_website_name())
        date_chosen = self.ar.date.strftime("%a, %B %d, %Y")

        extra_context = {
            'service': service,
            'staff_member': selected_sm,
            'all_staff_members': all_staff_members,
            'page_title': page_title,
            'page_description': page_description,
            'available_slots': [slot.strftime('%I:%M %p') for slot in available_slots],
            'date_chosen': date_chosen,
            'locale': get_locale(),
            'timezoneTxt': get_current_timezone_name(),
            'label': label,
            'rescheduled_date': self.ar.date.strftime("%Y-%m-%d"),
            'page_header': page_title,
            'ar_id_request': self.ar.id_request,
        }
        context.update(get_generic_context_with_extra(self.request, extra_context, admin=False))
        return context

    def get(self, request, *args, **kwargs):
        self.id_request = self.kwargs['id_request']
        self.ar = get_object_or_404(AppointmentRequest, id_request=self.id_request)
        if not can_appointment_be_rescheduled(self.ar):
            url = reverse('appointment:appointment_request', kwargs={'service_id': self.ar.service.id})
            context = get_generic_context_with_extra(self.request, {'url': url, }, admin=False)
            logger.error(f"Appointment with id_request {self.id_request} cannot be rescheduled")
            return render(self.request, 'error_pages/403_forbidden_rescheduling.html', context=context, status=403)
        return super().get(request, *args, **kwargs)


prepare_reschedule_appointment = PrepareRescheduleAppointment.as_view()


class RescheduleAppointmentSubmitView(TemplateView):
    template_name = "appointment/appointments.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        form = AppointmentRequestForm()
        extra_context = {'form': form}
        context.update(get_generic_context_with_extra(self.request, extra_context, admin=False))
        return context

    def post(self, request, *args, **kwargs):
        form = AppointmentRequestForm(request.POST)
        # get form values:
        ar_id_request = request.POST.get('appointment_request_id')
        ar = get_object_or_404(AppointmentRequest, id_request=ar_id_request)
        date_str = request.POST.get('date')
        date_ = convert_str_to_date(date_str)
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        sm_id = request.POST.get('staff_member')
        staff_member = get_object_or_404(StaffMember, id=sm_id)
        reason_for_rescheduling = request.POST.get('reason_for_rescheduling')
        if form.is_valid():
            arh = AppointmentRescheduleHistory.objects.create(
                appointment_request=ar,
                date=date_,
                start_time=start_time,
                end_time=end_time,
                staff_member=staff_member,
                reason_for_rescheduling=reason_for_rescheduling
            )
            messages.success(request, _("Appointment rescheduled successfully"))
            context = get_generic_context_with_extra(request, {}, admin=False)
            client_first_name = Appointment.objects.get(appointment_request=ar).client.first_name
            email = Appointment.objects.get(appointment_request=ar).client.email
            send_reschedule_confirmation_email(request=request, reschedule_history=arh, first_name=client_first_name,
                                               email=email, appointment_request=ar)
            return render(request, 'appointment/rescheduling_thank_you.html', context=context)
        messages.error(request, _("There was an error in your submission. Please check the form and try again."))
        return super().get(request, *args, **kwargs)


reschedule_appointment_submit = RescheduleAppointmentSubmitView.as_view()


class ConfirmRescheduleView(RedirectView):
    def get(self, request, *args, **kwargs):
        id_request = self.kwargs['id_request']
        self.reschedule_history = get_object_or_404(AppointmentRescheduleHistory, id_request=id_request)

        if self.reschedule_history.reschedule_status != 'pending' or not self.reschedule_history.still_valid():
            error_message = _("O-o-oh! This link is no longer valid.") if not self.reschedule_history.still_valid() else _(
                "O-o-oh! Can't find the pending reschedule request.")
            context = get_generic_context_with_extra(self.request, {"error_message": error_message}, admin=False)
            return render(self.request, 'error_pages/404_not_found.html', status=404, context=context)
        return super().get(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        ar = self.reschedule_history.appointment_request
        # Store previous details for logging or other purposes
        previous_details = {
            'date': ar.date,
            'start_time': ar.start_time,
            'end_time': ar.end_time,
            'staff_member': ar.staff_member,
        }

        # Update AppointmentRequest with new details
        ar.date = self.reschedule_history.date
        ar.start_time = self.reschedule_history.start_time
        ar.end_time = self.reschedule_history.end_time
        ar.staff_member = self.reschedule_history.staff_member
        ar.save(update_fields=['date', 'start_time', 'end_time', 'staff_member'])

        self.reschedule_history.date = previous_details['date']
        self.reschedule_history.start_time = previous_details['start_time']
        self.reschedule_history.end_time = previous_details['end_time']
        self.reschedule_history.staff_member = previous_details['staff_member']
        self.reschedule_history.reschedule_status = 'confirmed'
        self.reschedule_history.save(update_fields=['date', 'start_time', 'end_time', 'staff_member', 'reschedule_status'])

        messages.success(self.request, _("Appointment rescheduled successfully"))
        # notify admin and the concerned staff admin about client's rescheduling
        client_name = Appointment.objects.get(appointment_request=ar).client.get_full_name()
        notify_admin_about_reschedule(self.reschedule_history, ar, client_name)
        url = reverse('appointment:default_thank_you', kwargs={'appointment_id': ar.appointment.id})
        return url


confirm_reschedule = ConfirmRescheduleView.as_view()
