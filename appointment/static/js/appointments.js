const calendarEl = document.getElementById('calendar');
const nextAvailableDateSelector = $('.next-available-date')
const body = $('body');

const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    headerToolbar: {
        left: 'title',
        right: 'prev,today,next',
    },
    height: '400px',
    width: '80%',
    themeSystem: 'bootstrap',
    nowIndicator: true,
    bootstrapFontAwesome: {
        close: 'fa-times',
        prev: 'fa-chevron-left',
        next: 'fa-chevron-right',
        prevYear: 'fa-angle-double-left',
        nextYear: 'fa-angle-double-right'
    },
    color: 'black',
    selectable: true,
    dateClick: function (info) {
        // Convert the selected date string to a Date object
        const selectedDate = new Date(info.dateStr);

        // Get today's date
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const errorMessageContainer = $('.error-message');
        const appointmentSlot = $('.appointment-slot');
        // Check if the selected date is in the past
        getAvailableSlots(info.dateStr);
        if (selectedDate < today) {
            // Remove any existing error message
            errorMessageContainer.find('.no-availability-text').remove();
            appointmentSlot.remove();

            // Show an error message
            errorMessageContainer.append('<p class="no-availability-text">Date is in the past.</p>');

            // Disable the submit button
            $('.btn-submit-appointment').attr('disabled', 'disabled');
        } else {
            getAvailableSlots(info.dateStr);
        }

    },
    selectAllow: function (info) {
        return (info.start >= getDateWithoutTime(new Date()));
    },
});

calendar.setOption('locale', locale);

function getDateWithoutTime(dt) {
    dt.setHours(0, 0, 0, 0);
    return dt;
}

$(document).ready(function () {
    calendar.render();
    const currentDate = new Date().toISOString().slice(0, 10);
    getAvailableSlots(currentDate);
});

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
            if (data.available_slots.length === 0) {
                if (slotContainer.find('.no-availability-text').length === 0) {
                    slotContainer.append('<p class="no-availability-text">No availability</p>');
                }
                if (slotContainer.find('.btn-request-next-slot').length === 0) {
                    slotContainer.append(`<button class="btn btn-danger btn-request-next-slot" data-service-id="${serviceId}">Request next available slot</button>`);
                }
            } else {
                // remove the button to request for next available slot
                $('.no-availability-text').remove();
                $('.btn-request-next-slot').remove();
                nextAvailableDateSelector.remove();
                const uniqueSlots = [...new Set(data.available_slots)]; // remove duplicates
                for (let i = 0; i < uniqueSlots.length; i++) {
                    slotList.append('<li class="appointment-slot">' + uniqueSlots[i] + '</li>');
                }
            }
            // Update the date chosen
            $('.date_chosen').text(data.date_chosen);

            $('.appointment-slot').on('click', function () {
                // Remove the 'selected' class from all other appointment slots
                $('.appointment-slot').removeClass('selected');

                // Add the 'selected' class to the clicked appointment slot
                $(this).addClass('selected');

                // Enable the submit button
                $('.btn-submit-appointment').removeAttr('disabled');

                // Continue with the existing logic
                const selectedSlot = $(this).text();
                $('#service-datetime-chosen').text(data.date_chosen + ' ' + selectedSlot);
            });


        }
    });
}

body.on('click', '.btn-request-next-slot', function () {
    const serviceId = $(this).data('service-id');
    requestNextAvailableSlot(serviceId);
})

function requestNextAvailableSlot(serviceId) {
    const requestNextAvailableSlotURL = requestNextAvailableSlotURLTemplate.replace('0', serviceId);
    $.ajax({
        url: requestNextAvailableSlotURL,
        dataType: 'json',
        success: function (data) {
            // Set the date in the calendar to the next available date
            const nextAvailableDate = new Date(data.next_available_date);
            const formattedDate = new Intl.DateTimeFormat('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            }).format(nextAvailableDate);


            // Check if the .next-available-date element already exists
            if (nextAvailableDateSelector.length > 0) {
                // Update the content of the existing .next-available-date element
                nextAvailableDateSelector.text(`Next available date: ${formattedDate}`);
            } else {
                // If the .next-available-date element doesn't exist, create and append it
                const nextDateText = `<p class="next-available-date">Next available date: <br>${formattedDate}</p>`;
                $('.btn-request-next-slot').after(nextDateText);
            }
        }
    });
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

body.on('click', '.btn-submit-appointment', function () {
    const selectedSlot = $('.appointment-slot.selected').text();
    const selectedDate = $('.date_chosen').text();
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

        console.log("Submitting form...");
        form.submit();
    } else {
        console.log("No slot selected")
        const warningContainer = $('.warning-message');
        if (warningContainer.find('submit-warning') === 0) {
            warningContainer.append('<p class="submit-warning">Please select a time slot before submitting the appointment request.</p>');
        }
    }
});
