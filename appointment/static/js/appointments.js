const calendarEl = document.getElementById('calendar');
let nextAvailableDateSelector = $('.djangoAppt_next-available-date')
const body = $('body');

const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    headerToolbar: {
        left: 'title',
        right: 'prev,today,next',
    },
    height: '400px',
    themeSystem: 'bootstrap',
    nowIndicator: true,
    bootstrapFontAwesome: {
        close: 'fa-times',
        prev: 'fa-chevron-left',
        next: 'fa-chevron-right',
        prevYear: 'fa-angle-double-left',
        nextYear: 'fa-angle-double-right'
    },
    selectable: true,
    dateClick: function (info) {
        getAvailableSlots(info.dateStr);
    },
    selectAllow: function (info) {
        return (info.start >= getDateWithoutTime(new Date()));
    },
});

calendar.setOption('locale', locale);

$(document).ready(function () {
    calendar.render();
    const currentDate = new Date().toISOString().slice(0, 10);
    getAvailableSlots(currentDate);
});

body.on('click', '.djangoAppt_btn-request-next-slot', function () {
    const serviceId = $(this).data('service-id');
    requestNextAvailableSlot(serviceId);
})

body.on('click', '.btn-submit-appointment', function () {
    const selectedSlot = $('.djangoAppt_appointment-slot.selected').text();
    const selectedDate = $('.djangoAppt_date_chosen').text();
    if (!selectedSlot || !selectedDate) {
        alert('Please select a date and time');
        return;
    }
    if (selectedSlot && selectedDate) {
        const startTime = convertTo24Hour(selectedSlot);
        const APPOINTMENT_BASE_TEMPLATE = localStorage.getItem('APPOINTMENT_BASE_TEMPLATE');
        // Convert the selectedDate string to a valid format
        const dateParts = selectedDate.split(', ');
        const monthDayYear = dateParts[1] + "," + dateParts[2];
        const formattedDate = new Date(monthDayYear + " " + startTime);

        const date = formattedDate.toISOString().slice(0, 10);
        const endTimeDate = new Date(formattedDate.getTime() + serviceDuration * 60000);
        const endTime = formatTime(endTimeDate);

        const form = $('.appointment-form');

        form.append($('<input>', {type: 'hidden', name: 'date', value: date}));
        form.append($('<input>', {type: 'hidden', name: 'start_time', value: startTime}));
        form.append($('<input>', {type: 'hidden', name: 'end_time', value: endTime}));
        form.append($('<input>', {type: 'hidden', name: 'service', value: serviceId}));
        form.submit();
    } else {
        const warningContainer = $('.warning-message');
        if (warningContainer.find('submit-warning') === 0) {
            warningContainer.append('<p class="submit-warning">Please select a time slot before submitting the appointment request.</p>');
        }
    }
});

function getDateWithoutTime(dt) {
    dt.setHours(0, 0, 0, 0);
    return dt;
}

function convertTo24Hour(time12h) {
    const [time, modifier] = time12h.split(' ');
    let [hours, minutes] = time.split(':');

    if (hours === '12') {
        hours = '00';
    }

    if (modifier.toUpperCase() === 'PM') {
        hours = parseInt(hours, 10) + 12;
    }

    return `${hours}:${minutes}`;
}

function formatTime(date) {
    const hours = date.getHours();
    const minutes = date.getMinutes();
    return (hours < 10 ? '0' + hours : hours) + ':' + (minutes < 10 ? '0' + minutes : minutes);
}

function getAvailableSlots(selectedDate) {
    // Send an AJAX request to get the available slots for the selected date
    $.ajax({
        url: availableSlotsAjaxURL,
        data: {
            'selected_date': selectedDate,
        },
        dataType: 'json',
        success: function (data) {
            // Update the slot list with the available slots for the selected date
            const slotList = $('#slot-list');
            slotList.empty();
            const slotContainer = $('.slot-container');
            // Remove the "Next available date" message
            nextAvailableDateSelector = $('.djangoAppt_next-available-date'); // Update the selector
            nextAvailableDateSelector.remove();
            const errorMessageContainer = $('.error-message');

            if (data.available_slots.length === 0) {
                const selectedDateObj = moment.tz(selectedDate, timezone);
                const selectedD = selectedDateObj.toDate();
                const today = new Date();
                today.setHours(0, 0, 0, 0);

                if (selectedD < today) {
                    errorMessageContainer.find('.djangoAppt_no-availability-text').remove();
                    // Show an error message
                    errorMessageContainer.append('<p class="djangoAppt_no-availability-text">Date is in the past.</p>');
                    if (slotContainer.find('.djangoAppt_btn-request-next-slot').length === 0) {
                        slotContainer.append(`<button class="btn btn-danger djangoAppt_btn-request-next-slot" data-service-id="${serviceId}">Request next available slot</button>`);
                    }
                    // Disable the submit button
                    $('.btn-submit-appointment').attr('disabled', 'disabled');
                } else {
                    errorMessageContainer.find('.djangoAppt_no-availability-text').remove();
                    if (errorMessageContainer.find('.djangoAppt_no-availability-text').length === 0) {
                        errorMessageContainer.append('<p class="djangoAppt_no-availability-text">No availability</p>');
                    }
                    if (slotContainer.find('.djangoAppt_btn-request-next-slot').length === 0) {
                        slotContainer.append(`<button class="btn btn-danger djangoAppt_btn-request-next-slot" data-service-id="${serviceId}">Request next available slot</button>`);
                    }
                }
            } else {
                // remove the button to request for next available slot
                $('.djangoAppt_no-availability-text').remove();
                $('.djangoAppt_btn-request-next-slot').remove();
                const uniqueSlots = [...new Set(data.available_slots)]; // remove duplicates
                for (let i = 0; i < uniqueSlots.length; i++) {
                    slotList.append('<li class="djangoAppt_appointment-slot">' + uniqueSlots[i] + '</li>');
                }

                // Attach click event to the slots
                $('.djangoAppt_appointment-slot').on('click', function () {
                    // Remove the 'selected' class from all other appointment slots
                    $('.djangoAppt_appointment-slot').removeClass('selected');

                    // Add the 'selected' class to the clicked appointment slot
                    $(this).addClass('selected');

                    // Enable the submit button
                    $('.btn-submit-appointment').removeAttr('disabled');

                    // Continue with the existing logic
                    const selectedSlot = $(this).text();
                    $('#service-datetime-chosen').text(data.date_chosen + ' ' + selectedSlot);
                });
            }
            // Update the date chosen
            $('.djangoAppt_date_chosen').text(data.date_chosen);
        }
    });
}

function requestNextAvailableSlot(serviceId) {
    const requestNextAvailableSlotURL = requestNextAvailableSlotURLTemplate.replace('0', serviceId);
    $.ajax({
        url: requestNextAvailableSlotURL,
        dataType: 'json',
        success: function (data) {
            // Set the date in the calendar to the next available date
            const nextAvailableDateResponse = data.next_available_date;
            const selectedDateObj = moment.tz(nextAvailableDateResponse, timezone);
            const nextAvailableDate = selectedDateObj.toDate();
            const formattedDate = new Intl.DateTimeFormat('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            }).format(nextAvailableDate);

            // Check if the .next-available-date element already exists
            nextAvailableDateSelector = $('.djangoAppt_next-available-date'); // Update the selector
            if (nextAvailableDateSelector.length > 0) {
                // Update the content of the existing .next-available-date element
                nextAvailableDateSelector.text(`Next available date: ${formattedDate}`);
            } else {
                // If the .next-available-date element doesn't exist, create and append it
                const nextDateText = `<p class="djangoAppt_next-available-date">Next available date: <br>${formattedDate}</p>`;
                $('.djangoAppt_btn-request-next-slot').after(nextDateText);
            }
        }
    });
}
