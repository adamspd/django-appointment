# email_ops.py
# Path: appointment/utils/email_ops.py

"""
Author: Adams Pierre David
Since: 1.1.0
"""

from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.formats import date_format
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import gettext as _

from appointment import messages_ as email_messages
from appointment.email_sender import get_admins, notify_admin, send_email
from appointment.logger_config import get_logger
from appointment.models import (
    Appointment, AppointmentRequest, AppointmentRescheduleHistory, EmailVerificationCode, PasswordResetToken
)
from appointment.settings import APPOINTMENT_PAYMENT_URL
from appointment.utils.db_helpers import get_absolute_url_, get_site_url, get_website_name, username_in_user_model
from appointment.utils.ics_utils import generate_ics_file
from appointment.utils.template_helpers import get_email_template

logger = get_logger(__name__)


def get_email_context(appointment=None, appointment_request=None, request=None, site_url=None) -> dict:
    """
    What every email gets: the site's name and address and a link to the staff calendar, plus the appointment's
    objects and links when the email is about one.

    :param appointment: The appointment the email is about, if any.
    :param appointment_request: Its request, when there is no appointment yet.
    :param request: The request the email is sent from; the links start with its address.
    :param site_url: The site's address, for an email sent later without a request (the reminder).
    :return: The context. The emails add their own keys on top. Without a request or a site_url, links are relative.
    """
    if appointment is not None:
        appointment_request = appointment.appointment_request
    if site_url is None:
        site_url = get_site_url(request) if request is not None else ''

    def link(relative_url):
        return f"{site_url}{relative_url}"

    context = {
        'company': get_website_name(),
        'site_url': site_url,
        'current_year': timezone.localdate().year,
        'dashboard_url': link(reverse('appointment:get_user_appointments')),
    }
    if appointment_request is not None:
        context.update({
            'appointment_request': appointment_request,
            'service': appointment_request.service,
            'service_name': appointment_request.service.name,
            'staff_member': appointment_request.staff_member,
            'reschedule_url': link(
                reverse('appointment:prepare_reschedule_appointment', args=[appointment_request.get_id_request()])),
        })
    if appointment is not None:
        context.update({
            'appointment': appointment,
            'client': appointment.client,
            'client_name': appointment.get_client_name(),
            'appointment_url': link(reverse('appointment:display_appointment', args=[appointment.id])),
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


def get_thank_you_details(appointment):
    """
    The two tables of the thank-you email: the appointment's details, and the new account's details (None when the
    client already has a password, so the email doesn't offer to set one).
    """
    client = appointment.client
    appointment_details = {
        _('Service'): appointment.get_service_name(),
        _('Appointment Date'): appointment.get_appointment_date(),
        _('Appointment Time'): appointment.appointment_request.start_time,
        _('Duration'): appointment.get_service_duration()
    }
    if client.has_usable_password():
        return appointment_details, None
    account_details = {_('Email address'): client.email}
    if username_in_user_model():
        account_details[_('Username')] = client.username
    return appointment_details, account_details


def get_staff_name(staff_member) -> str:
    """The staff member's name for an email, or their username, email or id when they have none."""
    user = staff_member.user
    return (
            user.get_full_name() or
            (user.username if username_in_user_model() else None) or
            user.email or
            f"Staff Member {staff_member.id}"
    )


def get_set_password_link(user, request, expiration_minutes: int) -> str:
    """A new link for ``user`` to set their password, valid for ``expiration_minutes``."""
    token = PasswordResetToken.create_token(user=user, expiration_minutes=expiration_minutes)
    ui_db64 = urlsafe_base64_encode(force_bytes(user.pk))
    return get_absolute_url_(reverse('appointment:set_passwd', args=[ui_db64, token.token]), request=request)


# Each build_*_email function returns what an email is made of: {'template', 'subject', 'context'}. The send functions
# below and the preview page both use them, so the preview shows exactly what is sent.

def build_thank_you_email(appointment, user, request, appointment_details=None, account_details=None,
                          activation_link=None) -> dict:
    ar = appointment.appointment_request
    message = _("To enhance your experience, we have created a personalized account for you. It will allow "
                "you to manage your appointments, view service details, and make any necessary adjustments with ease.")
    context = get_email_context(appointment=appointment, request=request)
    context.update({
        'first_name': user.first_name,
        'message_1': get_thank_you_message(ar),
        'more_details': appointment_details,
        'account_details': account_details,
        'message_2': message if account_details is not None else None,
        # Month and year like "JAN 2021", in the active language, unlike strftime
        'month_year': date_format(ar.date, "M Y").upper(),
        'day': ar.date.strftime("%d"),
        'activation_link': activation_link,
        'main_title': _("Appointment successfully scheduled"),
        'reschedule_link': context['reschedule_url'],
    })
    return {
        # User must name their template 'thank_you.html' in their email directory
        'template': get_email_template('thank_you.html', 'email_sender/thank_you_email.html'),
        'subject': _("Thank you for booking us."),
        'context': context,
    }


def build_password_reset_email(user, request, activation_link, account_details=None) -> dict:
    if username_in_user_model() and hasattr(user, 'username'):
        login_instruction = _("To login, use username '{username}' or your email address.").format(
            username=user.username)
        username = user.username
    else:
        login_instruction = _("To login, use your email address.")
        username = ""
    context = get_email_context(request=request)
    context.update({
        'first_name': user.first_name,
        'activation_link': activation_link,
        'account_details': account_details if account_details else _("No additional details provided."),
        'username': username,
        'login_instruction': login_instruction,
        'user': user,
        'website_name': context['company'],
    })
    return {
        'template': get_email_template('password_reset.html', 'email_sender/password_reset_email.html'),
        'subject': _("Set Your Password for {company}").format(company=context['company']),
        'context': context,
    }


def build_new_appointment_email(appointment, client_name: str, recipient_name: str, is_staff_member: bool,
                                request=None) -> dict:
    staff_name = get_staff_name(appointment.get_staff_member())
    context = get_email_context(appointment=appointment, request=request)
    context.update({
        'recipient_name': recipient_name,
        'client_name': client_name,
        'is_staff_member': is_staff_member,
        'staff_member_name': staff_name,
    })
    return {
        # User must name their template 'new_appointment_admin_notification.html' in their email directory
        'template': get_email_template('new_appointment_admin_notification.html',
                                       'email_sender/admin_new_appointment_email.html'),
        'subject': _("New Appointment Request for %(client_name)s") % {'client_name': client_name},
        'context': context,
    }


def build_reminder_email(appointment, first_name, reschedule_link, recipient_type='client', site_url=None) -> dict:
    """The reminder sent the day before: to the client, or its copy to the admins (``recipient_type='admin'``)."""
    context = get_email_context(appointment=appointment, site_url=site_url)
    context.update({
        'first_name': first_name,
        'reschedule_link': reschedule_link,
        'recipient_type': recipient_type,
    })
    if recipient_type == 'admin':
        # The admin copy isn't addressed to the client: their first name stays available as client_first_name
        context.update({'first_name': '', 'client_first_name': first_name})
        subject = _("Admin Reminder: Upcoming Appointment")
    else:
        subject = _("Reminder: Upcoming Appointment")
    return {
        'template': get_email_template('reminder_email.html', 'email_sender/reminder_email.html'),
        'subject': subject,
        'context': context,
    }


def build_verification_email(user, code, request=None) -> dict:
    context = get_email_context(request=request)
    context.update({
        'user': user,
        'first_name': user.first_name,
        'verification_code': code,
    })
    return {
        'template': get_email_template('verification.html', 'email_sender/verification_email.html'),
        'subject': _("Email Verification"),
        'context': context,
    }


def _reschedule_context(reschedule_history, appointment_request, request) -> dict:
    """What both reschedule emails show: the old and the new date and times."""
    context = get_email_context(
        appointment=Appointment.objects.filter(appointment_request=appointment_request).first(),
        appointment_request=appointment_request, request=request)
    context.update({
        'old_date': appointment_request.date,
        'reschedule_date': reschedule_history.date,
        'old_start_time': appointment_request.start_time,
        'start_time': reschedule_history.start_time,
        'old_end_time': appointment_request.end_time,
        'end_time': reschedule_history.end_time,
    })
    return context


def build_reschedule_confirmation_email(reschedule_history, appointment_request, first_name, request) -> dict:
    context = _reschedule_context(reschedule_history, appointment_request, request)
    context.update({
        'is_confirmation': True,
        'first_name': first_name,
        'confirmation_link': get_absolute_url_(
            reverse('appointment:confirm_reschedule', args=[reschedule_history.id_request]), request),
    })
    return {
        # User may name their template 'reschedule_confirmation_email.html' or 'reschedule.html'
        'template': get_email_template(('reschedule_confirmation_email.html', 'reschedule.html'),
                                       'email_sender/reschedule_email.html'),
        'subject': _("Confirm Your Appointment Rescheduling"),
        'context': context,
    }


def build_reschedule_admin_email(reschedule_history, appointment_request, client_name, request=None) -> dict:
    context = _reschedule_context(reschedule_history, appointment_request, request)
    context.update({
        'is_confirmation': False,
        'client_name': client_name,
        'reason_for_rescheduling': reschedule_history.reason_for_rescheduling,
    })
    return {
        # User may name their template 'notify_admin_about_reschedule_email.html' or 'reschedule_admin.html'
        'template': get_email_template(('notify_admin_about_reschedule_email.html', 'reschedule_admin.html'),
                                       'email_sender/reschedule_email.html'),
        'subject': _("Reschedule Request for %(client_name)s") % {'client_name': client_name},
        'context': context,
    }


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
    # if first time user, account details won't be none, thus creating a password reset link for the user
    set_passwd_link = get_set_password_link(user, request, 2880) if account_details else None  # 2 days
    appt = Appointment.objects.get(appointment_request=ar)
    appt.appointment_request = ar  # The caller's copy, as before: the email shows what it holds
    email_parts = build_thank_you_email(appt, user, request, appointment_details, account_details, set_passwd_link)
    send_email(
        recipient_list=[email],
        subject=email_parts['subject'],
        template_url=email_parts['template'],
        context=email_parts['context'],
        attachments=[('appointment.ics', generate_ics_file(appt), 'text/calendar')]
    )


def send_reset_link_to_staff_member(user, request, email: str, account_details=None):
    """Email the staff member to set a password.

    :param user: The staff member's user.
    :param email: The email address to send it to.
    :param account_details: Additional details about the account (default None).
    :param request: The request object.
    :return: None
    """
    set_passwd_link = get_set_password_link(user, request, 10080)  # 7 days
    email_parts = build_password_reset_email(user, request, set_passwd_link, account_details)
    send_email(
        recipient_list=[email],
        subject=email_parts['subject'],
        template_url=email_parts['template'],
        context=email_parts['context'],
    )


def notify_admin_about_appointment(appointment, client_name: str, request=None):
    """Tell the admins and the staff member about a new appointment."""
    logger.info(f"Sending notifications for new appointment {appointment.id}")

    staff_member = appointment.get_staff_member()
    staff_email = staff_member.user.email
    ics_attachment = [('appointment.ics', generate_ics_file(appointment), 'text/calendar')]
    staff_email_parts = build_new_appointment_email(appointment, client_name, get_staff_name(staff_member), True,
                                                    request)

    # Notify admins, once per address
    notified_emails = set()
    for admin_name, admin_email in get_admins():
        if admin_email in notified_emails:
            continue

        # A staff member who is also an admin gets the staff version, with the calendar file
        is_staff_admin = admin_email == staff_email
        email_parts = staff_email_parts if is_staff_admin else build_new_appointment_email(
            appointment, client_name, admin_name, False, request)
        notify_admin(
            subject=email_parts['subject'],
            template_url=email_parts['template'],
            context=email_parts['context'],
            recipient_email=admin_email,
            attachments=ics_attachment if is_staff_admin else None
        )
        notified_emails.add(admin_email)

    # Notify the staff member if they haven't been notified as an admin
    if staff_email not in notified_emails:
        logger.info(f"Notifying the staff member for new appointment {appointment.id}")
        send_email(
            recipient_list=[staff_email],
            subject=staff_email_parts['subject'],
            template_url=staff_email_parts['template'],
            context=staff_email_parts['context'],
            attachments=ics_attachment
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
    email_parts = build_verification_email(user, code, request)
    send_email(
        recipient_list=[email],
        subject=email_parts['subject'],
        template_url=email_parts['template'],
        context=email_parts['context'],
        request=request
    )


def send_reschedule_confirmation_email(request, reschedule_history, appointment_request, first_name: str, email: str):
    """Ask the client to confirm the new date of their appointment."""
    email_parts = build_reschedule_confirmation_email(reschedule_history, appointment_request, first_name, request)
    send_email(
        recipient_list=[email],
        subject=email_parts['subject'],
        template_url=email_parts['template'],
        context=email_parts['context']
    )


def notify_admin_about_reschedule(reschedule_history, appointment_request, client_name: str, request=None):
    """Notify the admin and the staff member about a rescheduled appointment request."""
    logger.info(f"Sending reschedule notifications for appointment {appointment_request.id}")

    email_parts = build_reschedule_admin_email(reschedule_history, appointment_request, client_name, request)
    appt = Appointment.objects.get(appointment_request=appointment_request)
    attachments = [('appointment.ics', generate_ics_file(appt), 'text/calendar')]
    staff_member = appointment_request.staff_member

    notify_admin(subject=email_parts['subject'], template_url=email_parts['template'],
                 context=email_parts['context'], attachments=attachments)

    # The staff member already got the admin email if they are one
    if staff_member.user.email not in [email for name, email in get_admins()]:
        send_email(recipient_list=[staff_member.user.email], subject=email_parts['subject'],
                   context=email_parts['context'], template_url=email_parts['template'], attachments=attachments)

    logger.info(f"Reschedule notifications sent for appointment {appointment_request.id}")


def get_preview_emails(appointment, request):
    """
    Every email the package sends, built for ``appointment`` by the same functions that send them, for the preview
    page. Nothing is saved: the links that need a token or a code show a sample instead.

    :return: ``{key: {'label', 'template', 'subject', 'context'}}``, in the order the emails are sent.
    """
    ar = appointment.appointment_request
    client = appointment.client
    staff_member = ar.staff_member
    sample_link = get_absolute_url_(reverse('appointment:get_user_appointments'), request)
    reschedule_link = get_absolute_url_(
        reverse('appointment:prepare_reschedule_appointment', args=[ar.get_id_request()]), request)
    site_url = get_site_url(request)
    # An unsaved reschedule to the next day, for the two reschedule emails
    reschedule_history = AppointmentRescheduleHistory(
        appointment_request=ar, date=ar.date + timezone.timedelta(days=1), start_time=ar.start_time,
        end_time=ar.end_time, staff_member=staff_member, reason_for_rescheduling=_("Example reason"))
    appointment_details, account_details = get_thank_you_details(appointment)

    emails = {
        'thank_you': (_("Booking confirmation (client)"), build_thank_you_email(
            appointment, client, request, appointment_details, account_details,
            sample_link if account_details else None)),
        'new_appointment': (_("New appointment (staff)"), build_new_appointment_email(
            appointment, client.first_name, get_staff_name(staff_member), True, request)),
        'reminder': (_("Reminder (client)"), build_reminder_email(
            appointment, client.first_name, reschedule_link, site_url=site_url)),
        'reminder_admin': (_("Reminder (admin)"), build_reminder_email(
            appointment, client.first_name, reschedule_link, 'admin', site_url=site_url)),
        'reschedule_confirmation': (_("Reschedule confirmation (client)"), build_reschedule_confirmation_email(
            reschedule_history, ar, client.first_name, request)),
        'reschedule_admin': (_("Reschedule (staff)"), build_reschedule_admin_email(
            reschedule_history, ar, appointment.get_client_name(), request)),
        'password_reset': (_("Set a password (staff)"), build_password_reset_email(
            staff_member.user, request, sample_link)),
        'verification': (_("Verification code (client)"), build_verification_email(client, 'A1B2C3', request)),
    }
    return {key: {'label': label, **parts} for key, (label, parts) in emails.items()}
