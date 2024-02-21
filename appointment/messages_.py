# email_messages.py
# Path: appointment/email_messages.py

"""
Author: Adams Pierre David
Since: 1.1.0
"""

from django.utils.translation import gettext as _

thank_you_no_payment = _("""We're excited to have you on board!""")

thank_you_payment_plus_down = _("""We're excited to have you on board! The next step is 
to pay for the booking. You have the choice to pay the whole amount or a down deposit.
If you choose the deposit, you will have to pay the rest of the amount on the day of the booking.""")

thank_you_payment = _("""We're excited to have you on board! Thank you for booking us. The next step is to pay for
the booking.""")

appt_updated_successfully = _("Appointment updated successfully.")

passwd_set_successfully = _("We've successfully set your password. You can now log in to your account.")

passwd_error = _("The password reset link is invalid or has expired.")
