const calendarEl = document.getElementById('calendar');
let nextAvailableDateSelector = $('.djangoAppt_next-available-date')
const body = $('body');
let nonWorkingDays = [];
let selectedDate = rescheduledDate || null;
let staffId = $('#staff_id').val() || null;
let previouslySelectedCell = null;
let isRequestInProgress = false;

const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    initialDate: selectedDate,
    timeZone: timezone,
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
        const day = info.date.getDay();  // Get the day of the week (0 for Sunday, 6 for Saturday)
        if (nonWorkingDays.includes(day)) {
            return;
        }

        // If there's a previously selected cell, remove the class
        if (previouslySelectedCell) {
            previouslySelectedCell.classList.remove('selected-cell');
        }

        // Add the class to the currently clicked cell
        info.dayEl.classList.add('selected-cell');

        // Store the currently clicked cell
        previouslySelectedCell = info.dayEl;

        selectedDate = info.dateStr;
        getAvailableSlots(info.dateStr, staffId);
    },
    datesSet: function (info) {
        highlightSelectedDate();
    },
    selectAllow: function (info) {
        const day = info.start.getDay();  // Get the day of the week (0 for Sunday, 6 for Saturday)
        if (nonWorkingDays.includes(day)) {
            return false;  // Disallow selection for non-working days
        }
        return (info.start >= getDateWithoutTime(new Date()));
    },
    dayCellClassNames: function (info) {
        const day = info.date.getDay();
        if (nonWorkingDays.includes(day)) {
            return ['disabled-day'];
        }
        return [];
    },
});

calendar.setOption('locale', locale);

$(document).ready(function () {
    staffId = $('#staff_id').val() || null;
    calendar.render();
    const currentDate = rescheduledDate || moment.tz(timezone).format('YYYY-MM-DD');
    getAvailableSlots(currentDate, staffId);
});

function highlightSelectedDate() {
    setTimeout(function () {
        const dateCell = document.querySelector(`.fc-daygrid-day[data-date='${selectedDate}']`);
        if (dateCell) {
            dateCell.classList.add('selected-cell');
            previouslySelectedCell = dateCell;
        }
    }, 10);
}

body.on('click', '.djangoAppt_btn-request-next-slot', function () {
    const serviceId = $(this).data('service-id');
    requestNextAvailableSlot(serviceId);
})

body.on('click', '.btn-submit-appointment', function () {
    const selectedSlot = $('.djangoAppt_appointment-slot.selected').text();
    const selectedDate = $('.djangoAppt_date_chosen').text();
    if (!selectedSlot || !selectedDate) {
        alert(selectDateAndTimeAlertTxt);
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
        const reasonForRescheduling = $('#reason_for_rescheduling').val();
        const form = $('.appointment-form');
        let formAction = rescheduledDate ? appointmentRescheduleURL : appointmentRequestSubmitURL;
        form.attr('action', formAction);
        if (!form.find('input[name="appointment_request_id"]').length) {
            form.append($('<input>', {
                type: 'hidden',
                name: 'appointment_request_id',
                value: appointmentRequestId
            }));
        }
        form.append($('<input>', {type: 'hidden', name: 'date', value: date}));
        form.append($('<input>', {type: 'hidden', name: 'start_time', value: startTime}));
        form.append($('<input>', {type: 'hidden', name: 'end_time', value: endTime}));
        form.append($('<input>', {type: 'hidden', name: 'service', value: serviceId}));
        form.append($('<input>', {type: 'hidden', name: 'reason_for_rescheduling', value: reasonForRescheduling}));
        form.submit();
    } else {
        const warningContainer = $('.warning-message');
        if (warningContainer.find('submit-warning') === 0) {
            warningContainer.append('<p class="submit-warning">' + selectTimeSlotWarningTxt + '</p>');
        }
    }
});

$('#staff_id').on('change', function () {
    staffId = $(this).val() || null;  // If staffId is an empty string, set it to null
    let currentDate = null
    if (selectedDate == null) {
        currentDate = moment.tz(timezone).format('YYYY-MM-DD');
    } else {
        currentDate = selectedDate;
    }
    fetchNonWorkingDays(staffId, function (newNonWorkingDays) {
        nonWorkingDays = newNonWorkingDays;  // Update the nonWorkingDays array
        calendar.render();  // Re-render the calendar to apply changes

        // Fetch available slots for the current date
        getAvailableSlots(currentDate, staffId);
    });
});


function fetchNonWorkingDays(staffId, callback) {
    if (!staffId || staffId === 'none') {
        nonWorkingDays = [];  // Reset nonWorkingDays
        calendar.render();   // Re-render the calendar
        callback([]);
        return;  // Exit the function early
    }
    let ajaxData = {
        'staff_member': staffId,
    };

    $.ajax({
        url: getNonWorkingDaysURL,
        data: ajaxData,
        dataType: 'json',
        success: function (data) {
            if (data.error) {
                console.error('Error fetching non-working days:', data.message);
                callback([]);
            } else {
                nonWorkingDays = data.non_working_days;
                calendar.render();
                callback(data.non_working_days);
            }
        }
    });
}

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

function getAvailableSlots(selectedDate, staffId = null) {
    // Update the slot list with the available slots for the selected date
    const slotList = $('#slot-list');
    const slotContainer = $('.slot-container');
    const errorMessageContainer = $('.error-message');

    // Clear previous error messages and slots
    slotList.empty();
    errorMessageContainer.find('.djangoAppt_no-availability-text').remove();

    // Remove the "Next available date" message
    nextAvailableDateSelector = $('.djangoAppt_next-available-date'); // Update the selector
    nextAvailableDateSelector.remove();

    // Correctly check if staffId is 'none', null, or undefined and exit the function if true
    // Check if 'staffId' is 'none', null, or undefined and display an error message
    if (staffId === 'none' || staffId === null || staffId === undefined) {
        console.log('No staff ID provided, displaying error message.');
        const errorMessage = $('<p class="djangoAppt_no-availability-text">' + noStaffMemberSelectedTxt + '</p>');
        errorMessageContainer.append(errorMessage);
        // Optionally disable the "submit" button here
        $('.btn-submit-appointment').attr('disabled', 'disabled');
        return; // Exit the function early
    }

    let ajaxData = {
        'selected_date': selectedDate,
        'staff_member': staffId,
    };
    fetchNonWorkingDays(staffId, function (nonWorkingDays) {
        // Check if nonWorkingDays is an array
        if (Array.isArray(nonWorkingDays)) {
            // Update the FullCalendar configuration
            // calendar.setOption('hiddenDays', nonWorkingDays);
        } else {
            // Handle the case where there's an error or no data
            // For now, we'll just log it, but you can handle it more gracefully if needed
            console.error('Failed to get non-working days:', nonWorkingDays);
        }
    });

    // Send an AJAX request to get the available slots for the selected date
    if (isRequestInProgress) {
        return; // Exit the function if a request is already in progress
    }
    isRequestInProgress = true;
    $.ajax({
        url: availableSlotsAjaxURL,
        data: ajaxData,
        dataType: 'json',
        success: function (data) {
            if (data.available_slots.length === 0) {
                const selectedDateObj = moment.tz(selectedDate, timezone);
                const selectedD = selectedDateObj.toDate();
                const today = new Date();
                today.setHours(0, 0, 0, 0);

                if (selectedD < today) {
                    // Show an error message
                    errorMessageContainer.append('<p class="djangoAppt_no-availability-text">' + dateInPastErrorTxt + '</p>');
                    if (slotContainer.find('.djangoAppt_btn-request-next-slot').length === 0) {
                        slotContainer.append(`<button class="btn btn-danger djangoAppt_btn-request-next-slot" data-service-id="${serviceId}">` + requestNonAvailableSlotBtnTxt + `</button>`);
                    }
                    // Disable the 'submit' button
                    $('.btn-submit-appointment').attr('disabled', 'disabled');
                } else {
                    errorMessageContainer.find('.djangoAppt_no-availability-text').remove();
                    if (errorMessageContainer.find('.djangoAppt_no-availability-text').length === 0) {
                        errorMessageContainer.append(`<p class="djangoAppt_no-availability-text">${data.message}</p>`);
                    }
                    // Check if the returned message is 'No availability'
                    if (data.message.toLowerCase() === 'no availability') {
                        if (slotContainer.find('.djangoAppt_btn-request-next-slot').length === 0) {
                            slotContainer.append(`<button class="btn btn-danger djangoAppt_btn-request-next-slot" data-service-id="${serviceId}">` + requestNonAvailableSlotBtnTxt + `</button>`);
                        }
                    } else {
                        $('.djangoAppt_btn-request-next-slot').remove();
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
            $('#service-datetime-chosen').text(data.date_chosen);
            isRequestInProgress = false;
        },
        error: function() {
            isRequestInProgress = false; // Ensure the flag is reset even if the request fails
        }
    });
}

function requestNextAvailableSlot(serviceId) {
    const requestNextAvailableSlotURL = requestNextAvailableSlotURLTemplate.replace('0', serviceId);
    if (staffId === null) {
        return;
    }
    let ajaxData = {
        'staff_member': staffId,
    };
    $.ajax({
        url: requestNextAvailableSlotURL,
        data: ajaxData,
        dataType: 'json',
        success: function (data) {
            // If there's an error, just log it and return
            let nextAvailableDateResponse = null;
            let formattedDate = null;
            if (data.error) {
                nextAvailableDateResponse = data.message;
            } else {
                // Set the date in the calendar to the next available date
                nextAvailableDateResponse = data.next_available_date;
                const selectedDateObj = moment.tz(nextAvailableDateResponse, timezone);
                const nextAvailableDate = selectedDateObj.toDate();
                formattedDate = new Intl.DateTimeFormat('en-US', {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric'
                }).format(nextAvailableDate);
            }

            // Check if the .next-available-date element already exists
            nextAvailableDateSelector = $('.djangoAppt_next-available-date'); // Update the selector
            let nextAvailableDateText = null;
            if (data.error) {
                nextAvailableDateText = nextAvailableDateResponse;
            } else {
                nextAvailableDateText = `Next available date: ${formattedDate}`;
            }
            if (nextAvailableDateSelector.length > 0) {
                // Update the content of the existing .next-available-date element
                nextAvailableDateSelector.text(nextAvailableDateText);
            } else {
                // If the .next-available-date element doesn't exist, create and append it
                const nextDateText = `<p class="djangoAppt_next-available-date">${nextAvailableDateText}</p>`;
                $('.djangoAppt_btn-request-next-slot').after(nextDateText);
            }
        }
    });
}
