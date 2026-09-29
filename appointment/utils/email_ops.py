# email_ops.py
# Path: appointment/utils/email_ops.py

"""
Author: Adams Pierre David
Since: 1.1.0
"""

from django.template.exceptions import TemplateDoesNotExist
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.formats import date_format
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext as _

from appointment import messages_ as email_messages
from appointment.email_sender import get_admins, notify_admin, send_email
from appointment.logger_config import get_logger
from appointment.models import Appointment, AppointmentRequest, EmailVerificationCode, PasswordResetToken
from appointment.settings import APPOINTMENT_PAYMENT_URL
from appointment.utils.db_helpers import (
    build_absolute_url, get_absolute_url_, get_site_url, get_website_name, username_in_user_model
)
from appointment.utils.ics_utils import generate_ics_file
from appointment.utils.template_helpers import get_email_template

logger = get_logger(__name__)


def get_email_context(appointment=None, appointment_request=None, request=None) -> dict:
    """
    What every email gets: the site's name and address and a link to the staff calendar, plus the appointment's
    objects and links when the email is about one.

    :param appointment: The appointment the email is about, if any.
    :param appointment_request: Its request, when there is no appointment yet.
    :param request: The request, when there is one; used for the links when ``APPOINTMENT_SITE_URL`` isn't set.
    :return: The context. The emails add their own keys on top.
    """
    if appointment is not None:
        appointment_request = appointment.appointment_request
    context = {
        'company': get_website_name(),
        'site_url': get_site_url(request),
        'current_year': timezone.localdate().year,
        'dashboard_url': build_absolute_url(reverse('appointment:get_user_appointments'), request),
    }
    if appointment_request is not None:
        context.update({
            'appointment_request': appointment_request,
            'service': appointment_request.service,
            'service_name': appointment_request.service.name,
            'staff_member': appointment_request.staff_member,
            'reschedule_url': build_absolute_url(
                reverse('appointment:prepare_reschedule_appointment', args=[appointment_request.get_id_request()]),
                request),
        })
    if appointment is not None:
        context.update({
            'appointment': appointment,
            'client': appointment.client,
            'client_name': appointment.get_client_name(),
            'appointment_url': build_absolute_url(
                reverse('appointment:display_appointment', args=[appointment.id]), request),
        })
    return context


def get_thank_you_message(ar: AppointmentRequest) -> str:
    """
    Get the appropriate email message based on the appointment request.

    If the payment URL is not set (APPOINTMENT_PAYMENT_URL is None), it returns the thank_you_no_payment message.
    If the appointment request accepts down payment, it returns the thank_you_payment_plus_down message.
    Otherwise, it returns the thank_you_payment message.

    :param ar: The appointment request.
    :return: The appropriate email message.
    """
    if APPOINTMENT_PAYMENT_URL is None:
        message = email_messages.thank_you_no_payment
    elif ar.accepts_down_payment():
        message = email_messages.thank_you_payment_plus_down
    else:
        message = email_messages.thank_you_payment
    return message


def send_thank_you_email(ar: AppointmentRequest, user, request, email: str, appointment_details=None,
                         account_details=None):
    """Send a thank-you email to the client for booking an appointment.

    :param ar: The 'appointment request' associated with the booking.
    :param user: The user who booked the appointment.
    :param email: The email address of the client.
    :param appointment_details: Additional details about the appointment (default None).
    :param account_details: Additional details about the account (default None).
    :param request: The request object.
    :return: None
    """
    # Month and year like "J A N 2 0 2 1"
    month_year = date_format(ar.date, "M Y").upper()  # In the active language, unlike strftime
    day = ar.date.strftime("%d")

    # if first time user, account details won't be none, thus creating a password reset link for the user
    set_passwd_link = None
    if account_details:
        token = PasswordResetToken.create_token(user=user, expiration_minutes=2880)  # 2-day expiration
        ui_db64 = urlsafe_base64_encode(force_bytes(user.pk))
        relative_set_passwd_link = reverse('appointment:set_passwd', args=[ui_db64, token.token])
        set_passwd_link = get_absolute_url_(relative_set_passwd_link, request=request)

    relative_reschedule_url = reverse('appointment:prepare_reschedule_appointment', args=[ar.get_id_request()])
    reschedule_link = get_absolute_url_(relative_reschedule_url, request)

    message = _("To enhance your experience, we have created a personalized account for you. It will allow "
                "you to manage your appointments, view service details, and make any necessary adjustments with ease.")

    # let's get the ics file
    appt = Appointment.objects.get(appointment_request=ar)
    ics_file = generate_ics_file(appt)

    email_context = {
        **get_email_context(appointment=appt, request=request),
        'first_name': user.first_name,
        'message_1': get_thank_you_message(ar),
        'current_year': timezone.localdate().year,
        'company': get_website_name(),
        'more_details': appointment_details,
        'account_details': account_details,
        'message_2': message if account_details is not None else None,
        'month_year': month_year,
        'day': day,
        'activation_link': set_passwd_link,
        'main_title': _("Appointment successfully scheduled"),
        'reschedule_link': reschedule_link,
    }

    # User must name their template 'thank_you.html' in their email directory
    template_path = get_email_template('thank_you.html', 'email_sender/thank_you_email.html')

    send_email(
        recipient_list=[email],
        subject=_("Thank you for booking us."),
        template_url=template_path,
        context=email_context,
        attachments=[('appointment.ics', ics_file, 'text/calendar')]
    )


def send_reset_link_to_staff_member(user, request, email: str, account_details=None):
    """Email the staff member to set a password.

    :param user: The user who booked the appointment.
    :param email: The email address of the client.
    :param account_details: Additional details about the account (default None).
    :param request: The request object.
    :return: None
    """
    token = PasswordResetToken.create_token(user=user, expiration_minutes=10080)  # 7 days expiration
    ui_db64 = urlsafe_base64_encode(force_bytes(user.pk))
    relative_set_passwd_link = reverse('appointment:set_passwd', args=[ui_db64, token.token])
    set_passwd_link = get_absolute_url_(relative_set_passwd_link, request=request)
    website_name = get_website_name()

    # Get username safely
    if username_in_user_model() and hasattr(user, 'username'):
        login_instruction = _("To login, use username '{username}' or your email address.").format(
            username=user.username)
        username = user.username
    else:
        login_instruction = _("To login, use your email address.")
        username = ""

    # Try the custom template first, then the default one; plain text only if both fail
    try:
        template_path = get_email_template('password_reset.html', 'email_sender/password_reset_email.html')
        if template_path:
            email_context = {
                **get_email_context(request=request),
                'first_name': user.first_name,
                'current_year': timezone.localdate().year,
                'company': website_name,
                'activation_link': set_passwd_link,
                'account_details': account_details if account_details else _("No additional details provided."),
                'username': username,
                'login_instruction': login_instruction,
                'user': user,
                'website_name': website_name,
            }
            send_email(
                recipient_list=[email],
                subject=_("Set Your Password for {company}").format(company=website_name),
                template_url=template_path,
                context=email_context,
            )
        else:
            raise TemplateDoesNotExist("password_reset.html")
    except TemplateDoesNotExist:
        message = _("""
            Hello {first_name},

            A request has been received to set a password for your staff account for the year {current_year} at {company}.

            Please click the link below to set up your new password:
            {activation_link}

            {login_instruction}

            If you did not request this, please ignore this email.

            {account_details}

            Regards,
            {company}
            """).format(
            first_name=user.first_name,
            current_year=timezone.localdate().year,
            company=website_name,
            activation_link=set_passwd_link,
            login_instruction=login_instruction,
            account_details=account_details if account_details else _("No additional details provided.")
        )

        send_email(
            recipient_list=[email],
            subject=_("Set Your Password for {company}").format(company=website_name),
            message=message,
        )


def notify_admin_about_appointment(appointment, client_name: str):
    """Notify admin with custom template support."""

    logger.info(f"Sending notifications for new appointment {appointment.id}")

    staff_member = appointment.get_staff_member()
    ics_file = generate_ics_file(appointment)

    # Create a set to keep track of notified email addresses
    notified_emails = set()

    # Prepare the staff member notification
    staff_email = staff_member.user.email
    staff_name = (
            staff_member.user.get_full_name() or
            (staff_member.user.username if username_in_user_model() else None) or
            staff_member.user.email or
            f"Staff Member {staff_member.id}"
    )

    # User must name their template 'new_appointment_admin_notification.html' in their email directory
    template_path = get_email_template('new_appointment_admin_notification.html',
                                       'email_sender/admin_new_appointment_email.html')
    common_context = get_email_context(appointment=appointment)
    staff_context = {
        **common_context,
        'recipient_name': staff_name,
        'client_name': client_name,
        'appointment': appointment,
        'is_staff_member': True,
        'staff_member_name': staff_name
    }

    # Notify admins
    for admin_name, admin_email in get_admins():
        if admin_email in notified_emails:
            continue  # Skip if this email has already been notified

        is_staff_admin = admin_email == staff_email
        email_context = staff_context if is_staff_admin else {
            **common_context,
            'recipient_name': admin_name,
            'client_name': client_name,
            'appointment': appointment,
            'is_staff_member': False,
            'staff_member_name': staff_name
        }

        subject = _("New Appointment Request for %(client_name)s") % {'client_name': client_name}
        attachments = [('appointment.ics', ics_file, 'text/calendar')] if is_staff_admin else None

        notify_admin(
            subject=subject,
            template_url=template_path,
            context=email_context,
            recipient_email=admin_email,
            attachments=attachments
        )

        notified_emails.add(admin_email)

    # Notify staff member if they haven't been notified as an admin
    if staff_email not in notified_emails:
        logger.info(f"Notifying the staff member for new appointment {appointment.id}")
        send_email(
            recipient_list=[staff_email],
            subject=_("New Appointment Request for %(client_name)s") % {'client_name': client_name},
            template_url=template_path,
            context=staff_context,
            attachments=[('appointment.ics', ics_file, 'text/calendar')]
        )

    logger.info(f"Notifications sent for appointment {appointment.id}")


def send_verification_email(user, email: str, request=None):
    """
    Send an email with a verification code to the user for email verification.

    Generates a verification code using the EmailVerificationCode model and sends it to the user's email.

    :param user: The user to verify the email address.
    :param email: The email address of the user.
    :param request: (optional) Without the request, send_email cannot render the email template with custom context_processors.
    :return: None
    """
    code = EmailVerificationCode.generate_code(user=user)

    # Try the custom template first, then the default one; plain text only if both fail
    try:
        template_path = get_email_template('verification.html', 'email_sender/verification_email.html')
        if template_path:
            email_context = {
                **get_email_context(request=request),
                'user': user,
                'first_name': user.first_name,
                'verification_code': code,
                'company': get_website_name(),
            }
            send_email(
                recipient_list=[email],
                subject=_("Email Verification"),
                template_url=template_path,
                context=email_context,
                request=request
            )
        else:
            raise TemplateDoesNotExist("verification.html")
    except TemplateDoesNotExist:
        # Original plain text behavior
        message = _("Your verification code is {code}.").format(code=code)
        send_email(recipient_list=[email], subject=_("Email Verification"), message=message)


def send_reschedule_confirmation_email(request, reschedule_history, appointment_request, first_name: str, email: str):
    """Send reschedule email with custom template support."""

    relative_confirmation_link = reverse('appointment:confirm_reschedule', args=[reschedule_history.id_request])
    confirmation_link = get_absolute_url_(relative_confirmation_link, request)

    email_context = {
        **get_email_context(appointment=Appointment.objects.filter(appointment_request=appointment_request).first(),
                            appointment_request=appointment_request, request=request),
        'is_confirmation': True,
        'first_name': first_name,
        'old_date': appointment_request.date,
        'reschedule_date': reschedule_history.date,
        'old_start_time': appointment_request.start_time,
        'start_time': reschedule_history.start_time,
        'old_end_time': appointment_request.end_time,
        'end_time': reschedule_history.end_time,
        'confirmation_link': confirmation_link,
        'company': get_website_name(),
    }

    # User may name their template 'reschedule_confirmation_email.html' or 'reschedule.html'
    template_path = get_email_template(
        ('reschedule_confirmation_email.html', 'reschedule.html'),
        'email_sender/reschedule_email.html'
    )
    subject = _("Confirm Your Appointment Rescheduling")

    send_email(
        recipient_list=[email],
        subject=subject,
        template_url=template_path,
        context=email_context
    )


def notify_admin_about_reschedule(reschedule_history, appointment_request, client_name: str):
    """Notify the admin and the staff member about a rescheduled appointment request."""
    logger.info(f"Sending reschedule notifications for appointment {appointment_request.id}")

    # Assuming you have a way to fetch these additional details
    service_name = appointment_request.service.name
    reason_for_rescheduling = reschedule_history.reason_for_rescheduling

    # let's get the new ics file
    appt = Appointment.objects.get(appointment_request=appointment_request)
    ics_file = generate_ics_file(appt)

    email_context = {
        **get_email_context(appointment=appt),
        'is_confirmation': False,
        'client_name': client_name,
        'service_name': service_name,
        'reason_for_rescheduling': reason_for_rescheduling,
        'old_date': appointment_request.date,
        'reschedule_date': reschedule_history.date,
        'old_start_time': appointment_request.start_time,
        'start_time': reschedule_history.start_time,
        'old_end_time': appointment_request.end_time,
        'end_time': reschedule_history.end_time,
        'company': get_website_name(),
    }

    subject = _("Reschedule Request for %(client_name)s") % {'client_name': client_name}
    staff_member = appointment_request.staff_member

    # User may name their template 'notify_admin_about_reschedule_email.html' or 'reschedule_admin.html'
    template_path = get_email_template(
        ('notify_admin_about_reschedule_email.html', 'reschedule_admin.html'),
        'email_sender/reschedule_email.html'
    )

    # Notifying admin
    notify_admin(subject=subject, template_url=template_path, context=email_context,
                 attachments=[('appointment.ics', ics_file, 'text/calendar')])

    # The staff member already got the admin email if they are one
    if staff_member.user.email not in [email for name, email in get_admins()]:
        send_email(recipient_list=[staff_member.user.email], subject=subject, context=email_context,
                   template_url=template_path,
                   attachments=[('appointment.ics', ics_file, 'text/calendar')])

    logger.info(f"Reschedule notifications sent for appointment {appointment_request.id}")


def get_preview_emails(appointment, request):
    """
    Every email the package sends, built for ``appointment`` as it would be sent, for the preview page.

    :return: ``{key: {'label', 'template', 'subject', 'context'}}``, in the order the emails are sent.
    """
    ar = appointment.appointment_request
    client = appointment.client
    base = get_email_context(appointment=appointment, request=request)
    staff_name = ar.staff_member.get_staff_member_name()
    sample_link = build_absolute_url(reverse('appointment:get_user_appointments'), request)
    new_date = ar.date + timezone.timedelta(days=1)
    reschedule = {
        'old_date': ar.date, 'reschedule_date': new_date, 'old_start_time': ar.start_time,
        'start_time': ar.start_time, 'old_end_time': ar.end_time, 'end_time': ar.end_time,
    }

    def email(label, names, default, subject, context):
        return {'label': label, 'template': get_email_template(names, default), 'subject': subject,
                'context': {**base, **context}}

    return {
        'thank_you': email(
            _("Booking confirmation (client)"), 'thank_you.html', 'email_sender/thank_you_email.html',
            _("Thank you for booking us."), {
                'first_name': client.first_name, 'message_1': get_thank_you_message(ar),
                'more_details': {_('Service'): appointment.get_service_name(),
                                 _('Appointment Date'): appointment.get_appointment_date(),
                                 _('Appointment Time'): ar.start_time,
                                 _('Duration'): appointment.get_service_duration()},
                'account_details': {_('Email address'): client.email},
                'month_year': date_format(ar.date, "M Y").upper(), 'day': ar.date.strftime("%d"),
                'activation_link': sample_link, 'main_title': _("Appointment successfully scheduled"),
                'reschedule_link': base['reschedule_url'],
            }),
        'new_appointment': email(
            _("New appointment (staff)"), 'new_appointment_admin_notification.html',
            'email_sender/admin_new_appointment_email.html',
            _("New Appointment Request for %(client_name)s") % {'client_name': base['client_name']}, {
                'recipient_name': staff_name, 'is_staff_member': True, 'staff_member_name': staff_name,
            }),
        'reminder': email(
            _("Reminder (client)"), 'reminder_email.html', 'email_sender/reminder_email.html',
            _("Reminder: Upcoming Appointment"), {
                'first_name': client.first_name, 'reschedule_link': base['reschedule_url'],
                'recipient_type': 'client',
            }),
        'reminder_admin': email(
            _("Reminder (admin)"), 'reminder_email.html', 'email_sender/reminder_email.html',
            _("Admin Reminder: Upcoming Appointment"), {
                'first_name': '', 'client_first_name': client.first_name, 'recipient_type': 'admin',
            }),
        'reschedule_confirmation': email(
            _("Reschedule confirmation (client)"), ('reschedule_confirmation_email.html', 'reschedule.html'),
            'email_sender/reschedule_email.html', _("Confirm Your Appointment Rescheduling"), {
                **reschedule, 'is_confirmation': True, 'first_name': client.first_name,
                'confirmation_link': sample_link,
            }),
        'reschedule_admin': email(
            _("Reschedule (staff)"), ('notify_admin_about_reschedule_email.html', 'reschedule_admin.html'),
            'email_sender/reschedule_email.html',
            _("Reschedule Request for %(client_name)s") % {'client_name': base['client_name']}, {
                **reschedule, 'is_confirmation': False, 'reason_for_rescheduling': _("Example reason"),
            }),
        'password_reset': email(
            _("Set a password (staff)"), 'password_reset.html', 'email_sender/password_reset_email.html',
            _("Set Your Password for {company}").format(company=base['company']), {
                'first_name': ar.staff_member.user.first_name, 'activation_link': sample_link,
                'login_instruction': _("To login, use your email address."), 'user': ar.staff_member.user,
                'account_details': _("No additional details provided."), 'website_name': base['company'],
            }),
        'verification': email(
            _("Verification code (client)"), 'verification.html', 'email_sender/verification_email.html',
            _("Email Verification"), {
                'first_name': client.first_name, 'user': client, 'verification_code': 'A1B2C3',
            }),
    }
