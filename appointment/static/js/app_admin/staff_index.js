// Constants
const MOBILE_WIDTH = 450;
const SMALL_TABLET_WIDTH = 650;
const TABLET_WIDTH = 767;
const MEDIUM_WIDTH = 991;

// Global variables
let eventIdSelected = null;
let calendar = null;
let isEditing = false;

document.addEventListener("DOMContentLoaded", initializeCalendar);
window.addEventListener('resize', updateCalendarConfig);

function initializeCalendar() {
    const formattedAppointments = formatAppointmentsForCalendar(appointments);
    const calendarEl = document.getElementById('calendar');
    calendar = new FullCalendar.Calendar(calendarEl, getCalendarConfig(formattedAppointments));
    calendar.setOption('locale', locale);
    calendar.render();
}

function formatAppointmentsForCalendar(appointments) {
    return appointments.map(appointment => ({
        id: appointment.id,
        title: appointment.service_name,
        start: appointment.start_time,
        end: appointment.end_time,
        client_name: appointment.client_name,
        backgroundColor: appointment.background_color,
    }));
}

function updateCalendarConfig() {
    calendar.setOption('headerToolbar', getHeaderToolbarConfig());
    calendar.setOption('height', getCalendarHeight());
}

function getCalendarConfig(events) {
    return {
        initialView: 'dayGridMonth',
        headerToolbar: getHeaderToolbarConfig(),
        navLinks: true,
        editable: true,
        dayMaxEvents: true,
        height: getCalendarHeight(),
        aspectRatio: 1.0,
        themeSystem: 'bootstrap5',
        nowIndicator: true,
        bootstrapFontAwesome: {
            close: 'fa-times',
            prev: 'fa-chevron-left',
            next: 'fa-chevron-right',
            prevYear: 'fa-angle-double-left',
            nextYear: 'fa-angle-double-right'
        },
        selectable: true,
        events: events,
        eventDisplay: 'block',
        timeZone: timezone,
        eventClick: async function (info) {
            eventIdSelected = info.event.id;
            await showEventModal(info.event);
        },
        dateClick: function (info) {
            // ... your code for dateClick ...
        },
        selectAllow: function (info) {
            // ... your code for selectAllow ...
        },
        dayCellClassNames: function (info) {
            // ... your code for dayCellClassNames ...
        },
        eventDrop: async function (info) {
            await validateAndUpdateAppointmentDate(info.event, info.revert);
        },
    };
}

function getHeaderToolbarConfig() {
    if (window.matchMedia('(max-width: 767px)').matches) {
        // Mobile configuration
        return {
            left: 'title',
            right: 'prev,next,dayGridMonth,timeGridDay'
        };
    } else if (window.matchMedia('(max-width: 991px)').matches) {
        // Tablet configuration
        return {
            left: 'prev,today,next',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        };
    } else {
        // Desktop configuration
        return {
            left: 'prevYear,prev,today,next,nextYear',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek',
            prevYear: 'prevYear',
            nextYear: 'nextYear'
        };
    }
}

function getCalendarHeight() {
    if (window.innerWidth <= MOBILE_WIDTH) return '500px';
    if (window.innerWidth <= SMALL_TABLET_WIDTH) return '600px';
    if (window.innerWidth <= TABLET_WIDTH) return '650px';
    if (window.innerWidth <= MEDIUM_WIDTH) return '767px';
    return '850px';
}

function toggleEditMode() {
    const modal = document.getElementById("eventDetailsModal");
    const inputs = modal.querySelectorAll("input");
    const servicesDropdown = document.getElementById("serviceSelect");

    // Retrieve the appointment that matches the eventIdSelected
    const appointment = appointments.find(app => Number(app.id) === Number(eventIdSelected));
    if (!appointment) {
        return;
    }

    const endTimeLabel = modal.querySelector("label[for='endTime']");  // Assuming you have a label with `for` attribute set to `endTime`
    const endTimeInput = modal.querySelector("input[name='endTime']");  // Assuming you have an input with `name` attribute set to `endTime`
    const editButton = document.getElementById("eventEditBtn");
    const submitButton = document.getElementById("eventSubmitBtn");
    const closeButton = modal.querySelector(".btn-secondary[data-dismiss='modal']");
    const cancelButton = document.getElementById("eventCancelBtn");

    if (isEditing) {
        inputs.forEach(input => input.disabled = true);
        servicesDropdown.disabled = true;
        endTimeLabel.style.display = "";  // Show the end time label
        endTimeInput.style.display = "";  // Show the end time input
        editButton.style.display = "";
        closeButton.style.display = "";
        submitButton.style.display = "none";
        cancelButton.style.display = "none";
    } else {
        inputs.forEach(input => input.disabled = false);
        servicesDropdown.disabled = false;
        endTimeLabel.style.display = "none";  // Hide the end time label
        endTimeInput.style.display = "none";  // Hide the end time input
        editButton.style.display = "none";
        closeButton.style.display = "none";
        submitButton.style.display = "";
        cancelButton.style.display = "";
    }

    isEditing = !isEditing;
}

function goToEvent() {
    // Get the event URL
    const event = appointments.find(app => Number(app.id) === Number(eventIdSelected));
    if (event && event.url) {
        closeModal()
        window.location.href = event.url;
    } else {
        console.error("Event not found or doesn't have a URL.");
    }
}

function closeModal() {
    const modal = document.getElementById("eventDetailsModal");
    const editButton = document.getElementById("eventEditBtn");
    const submitButton = document.getElementById("eventSubmitBtn");
    const closeButton = modal.querySelector(".btn-secondary[data-dismiss='modal']");
    const cancelButton = document.getElementById("eventCancelBtn");

    // Reset the modal buttons to their default state
    editButton.style.display = "";
    closeButton.style.display = "";
    submitButton.style.display = "none";
    cancelButton.style.display = "none";

    // Reset the editing flag
    isEditing = false;

    // Close the modal
    $('#eventDetailsModal').modal('hide');
}

function checkEmail(email) {
    const emailInput = document.querySelector('input[name="clientEmail"]');
    const emailError = document.getElementById("emailError");

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        emailInput.style.border = "1px solid red";
        emailError.textContent = "Invalid email address.";
        emailError.style.color = "red";
        emailError.style.display = "inline";  // Make the error message visible
        return false;
    } else {
        emailInput.style.border = "";  // Reset the border to its original style
        emailError.textContent = "";  // Clear the error message
        emailError.style.display = "none";  // Hide the error message
        return true;
    }
}

async function submitChanges() {
    const modal = document.getElementById("eventDetailsModal");
    const inputs = modal.querySelectorAll("input");
    const serviceDropdown = modal.querySelector("#serviceSelect");
    const serviceId = serviceDropdown.value;

    const data = {};

    inputs.forEach(input => {
        let key = input.previousElementSibling.innerText.trim().replace(/\s+/g, '_').replace(":", "").toLowerCase();
        data[key] = input.value;
    });

    // Check if the email is valid
    if (!checkEmail(data["client_email"])) {
        return;
    }

    data["appointment_id"] = eventIdSelected;  // Adding the appointment ID
    data["service_id"] = serviceId;

    try {
        const response = await fetch(updateApptMinInfoURL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',  // to ensure Django treats this as an AJAX request
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify(data)
        });
        if (response.ok) {
            const responseData = await response.json();

            if (responseData.appt) {
                const index = appointments.findIndex(app => Number(app.id) === Number(eventIdSelected));
                if (index !== -1) {
                    appointments[index] = responseData.appt;
                }
            }
            let eventToUpdate = calendar.getEventById(eventIdSelected);
            if (eventToUpdate) {
                eventToUpdate.setProp('title', responseData.appt.service_name);
                eventToUpdate.setStart(moment(responseData.appt.start_time).format('YYYY-MM-DDTHH:mm:ss'));
                eventToUpdate.setEnd(responseData.appt.end_time);
                eventToUpdate.setExtendedProp('client_name', responseData.appt.client_name);
                eventToUpdate.setProp('backgroundColor', responseData.appt.background_color);
                calendar.render();
            }
            calendar.refetchEvents();
            document.querySelector('input[name="startTime"]').value = responseData.appt.start_time;
            document.querySelector('input[name="endTime"]').value = responseData.appt.end_time;


        } else {
            console.error('Failed to update appointment. Server responded with:', response.status);
            // TODO: Handle error, e.g., show an error message to the user
        }
    } catch (error) {
        console.error('Failed to send data:', error);
        // TODO: Handle error, e.g., show an error message to the user
    }

    closeModal();
}

async function cancelEdit() {
    // Retrieve the appointment that matches the eventIdSelected
    const appointment = appointments.find(app => Number(app.id) === Number(eventIdSelected));
    if (!appointment) {
        return;
    }

    // Extract only the time using Moment.js
    const endTime = moment(appointment.end_time).format('HH:mm:ss');

    // Find the modal, end time label, and end time input
    const modal = document.getElementById("eventDetailsModal");
    const endTimeLabel = modal.querySelector("label[for='endTime']");
    const endTimeInput = modal.querySelector("input[name='endTime']");

    // Set and display the end time label and input
    endTimeInput.value = endTime;
    endTimeLabel.style.display = "";
    endTimeInput.style.display = "";

    // Re-show the event modal with the original data
    const event = {id: eventIdSelected};
    await showEventModal(event);
    toggleEditMode(); // Turn off edit mode
}

async function showEventModal(event) {
    const appointment = appointments.find(app => Number(app.id) === Number(event.id));
    if (!appointment) {
        return;
    }

    // Extract only the time using Moment.js
    const startTime = moment(appointment.start_time).format('HH:mm:ss');
    const endTime = moment(appointment.end_time).format('HH:mm:ss');

    // Fetch and populate services for dropdown
    const servicesDropdown = await populateServices(appointment.service_id);
    servicesDropdown.id = "serviceSelect";
    servicesDropdown.value = appointment.service_id; // Assuming you have a service_id in the appointment
    servicesDropdown.disabled = true; // Initially disable the dropdown

    // Convert the services dropdown to a string for the template
    const div = document.createElement('div');
    div.appendChild(servicesDropdown);
    const servicesDropdownString = div.innerHTML;

    // Set the content of the modal as input fields
    const modalBodyContent = `
        <label>Service Name:</label>
        ${servicesDropdownString}
        <label for="startTime">Start Time:</label>
        <input type="time" name="startTime" value="${startTime}" disabled>
        <label for="endTime">End Time:</label>
        <input type="time" name="endTime" value="${endTime}" disabled>
        <label for="clientName">Client Name:</label>
        <input type="text" name="clientName" value="${appointment.client_name}" disabled>
        <label for="clientEmail">Client Email</label>
        <input type="email" name="clientEmail" value="${appointment.client_email}" disabled>
        <span id="emailError" style="display:none;"></span>
        <label for="clientPhone">Phone Number</label>
        <input type="tel" name="clientPhone" value="${appointment.client_phone}" disabled>
        <label for="clientAddress">Client Address</label>
        <input type="text" name="clientAddress" value="${appointment.client_address}" disabled>
    `;

    document.getElementById('eventModalBody').innerHTML = modalBodyContent;

    // Display the modal
    $('#eventDetailsModal').modal('show');
}

function fetchServices() {
    let ajax_data_get_data = {
        'appointmentId': eventIdSelected,
    }
    const finalUrl = `${fetchServiceListForStaffURL}?${$.param(ajax_data_get_data)}`;
    return fetch(finalUrl)
        .then(response => response.json())
        .then(data => {
            return data.services_offered;  // This should be a list of dictionaries
        })
        .catch(error => {
            console.error("There was an error fetching the services.", error);
        });
}

async function populateServices(selectedServiceId) {
    const services = await fetchServices();
    const selectElement = document.createElement('select');
    services.forEach(service => {
        const option = document.createElement('option');
        option.value = service.id;  // Accessing the id
        option.textContent = service.name;  // Accessing the name
        if (service.id === selectedServiceId) {
            option.defaultSelected = true;
        }
        selectElement.appendChild(option);
    });
    return selectElement;
}

function getCSRFToken() {
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        return metaTag.getAttribute('content');
    } else {
        console.error("CSRF token meta tag not found!");
        return null;
    }
}


async function validateAndUpdateAppointmentDate(event, revertFunction) {
    const updatedStartTime = event.start.toISOString();
    const updatedEndTime = event.end ? event.end.toISOString() : null;

    const data = {
        appointment_id: event.id,
        start_time: updatedStartTime,
        date: event.start.toISOString().split('T')[0]
    };

    try {
        const validationResponse = await fetch(validateApptDateURL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify(data)
        });

        if (validationResponse.ok) {
            await updateAppointmentDate(event, revertFunction);
        } else {
            const responseData = await validationResponse.json();
            showErrorModal(responseData.message);

            revertFunction();
        }
    } catch (error) {
        console.error('Failed to validate data:', error);
        revertFunction();
    }
}

async function updateAppointmentDate(event, revertFunction) {
    const updatedStartTime = event.start.toISOString().split('T')[1];
    const updatedDate = event.start.toISOString().split('T')[0];

    const data = {
        appointment_id: event.id,
        start_time: updatedStartTime,
        date: updatedDate,
    };

    try {
        const response = await fetch(updateApptDateURL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            const responseData = await response.json();
            showErrorModal(responseData.message, 'Success')
            console.log('Appointment date updated:', responseData.message);
        } else {
            console.error('Failed to update appointment date. Server responded with:', response.statusText);
            revertFunction();
        }
    } catch (error) {
        console.error('Failed to send data:', error);
        revertFunction();
    }
}
