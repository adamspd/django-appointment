// Constants
const Constants = {
    MOBILE_WIDTH_SMALL: 350,
    MOBILE_WIDTH: 450,
    SMALL_TABLET_WIDTH: 650,
    TABLET_WIDTH: 767,
    MEDIUM_WIDTH: 991,
    DEFAULT_START_TIME: '09:00'
};

// Application State
const AppState = {
    eventIdSelected: null, calendar: null, isEditingAppointment: false, isCreating: false, isUserStaffAdmin: true,
};

document.addEventListener("DOMContentLoaded", initializeCalendar);
window.addEventListener('resize', updateCalendarConfig);
document.getElementById('eventDetailsModal').addEventListener('keypress', function (event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        document.getElementById('eventSubmitBtn').click();
    }
});

// Throttle resize events
let resizeTimeout;
window.addEventListener('resize', function () {
    if (resizeTimeout) {
        clearTimeout(resizeTimeout);
    }
    resizeTimeout = setTimeout(function () {
        initializeCalendar()
    }, 500); // Only rerender at most, every 100ms
});

document.addEventListener("DOMContentLoaded", function () {
    // Wait for a 50ms after the DOM is ready before initializing the calendar
    setUserStaffAdminFlag().then(() => {
        setTimeout(initializeCalendar, 50);
    });
});

const AppStateProxy = new Proxy(AppState, {
    set(target, property, value) {
        console.log(`Setting ${property} to ${value}`)
        // Check if the property being changed is 'isCreating'
        if (value === true) {
            attachEventListeners(); // Attach event listeners if isCreating becomes true
            // (didn't check if property is isCreating, since AppStateProxy is only set with it)
        }
        target[property] = value; // Set the property value
        return true; // Indicate successful setting
    }
});

function attachEventListeners() {
    // Checks if the DOM is already loaded
    if (document.readyState === "complete" || document.readyState === "interactive") {
        // DOM is already ready, attach event listeners directly
        attachEventListenersToDropdown();
    } else {
        // If the DOM is not yet ready, then wait for the DOMContentLoaded event
        document.addEventListener('DOMContentLoaded', function () {
            attachEventListenersToDropdown();
        });
    }
}

function attachEventListenersToDropdown() {
    const staffDropdown = document.getElementById('staffSelect');
    if (staffDropdown && !staffDropdown.getAttribute('listener-attached')) {
        staffDropdown.setAttribute('listener-attached', 'true');
        staffDropdown.addEventListener('change', async function () {
            const selectedStaffId = this.value;
            const servicesDropdown = document.getElementById('serviceSelect');
            const services = await fetchServicesForStaffMember(selectedStaffId);
            updateServicesDropdown(servicesDropdown, services);
        });
    }
}


function initializeCalendar() {
    const formattedAppointments = formatAppointmentsForCalendar(appointments);
    const calendarEl = document.getElementById('calendar');
    AppState.calendar = new FullCalendar.Calendar(calendarEl, getCalendarConfig(formattedAppointments));
    AppState.calendar.setOption('locale', locale);
    AppState.calendar.render();
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
    AppState.calendar.setOption('headerToolbar', getHeaderToolbarConfig());
    AppState.calendar.setOption('height', getCalendarHeight());
}

function mobileCheck() {
    return window.innerWidth < Constants.MOBILE_WIDTH;
}

function tabletCheck() {
    return window.innerWidth < Constants.TABLET_WIDTH;
}

function getEventDisplayedStyle() {
    if (mobileCheck()) {
        return "list-item";
    }
    return "block";
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
        defaultView: mobileCheck() ? "basicDay" : "dayGridMonth",
        selectable: true,
        events: events,
        eventDisplay: getEventDisplayedStyle(),
        timeZone: timezone,
        eventClick: async function (info) {
            AppState.eventIdSelected = info.event.id;
            await showEventModal(info.event.id, false, false);
        },
        dateClick: function (info) {
            // Retrieve events for the clicked date
            const dateEvents = appointments
                .filter(event => moment(info.date).isSame(event.start_time, 'day'))
                .sort((a, b) => new Date(a.start_time) - new Date(b.start_time));

            // Display events in a list below the calendar
            displayEventList(dateEvents, info.date);
        },

        selectAllow: function (info) {
        },
        dayCellClassNames: function (info) {
            const day = info.date.getDay();
            if (day === 0 || day === 6) { // 0 = Sunday, 6 = Saturday
                return 'highlight-weekend';
            }
            return ''; // Return empty string for regular days
        },
        eventDrop: async function (info) {
            await validateAndUpdateAppointmentDate(info.event, info.revert);
        },
        eventDidMount: function (info) {
            // If it is a mobile view, we change the event to a dot
            if (mobileCheck()) {
                // Find the fc-daygrid-event-dot class within the event element
                // and change its style to display as a dot
                const dotEl = info.el.querySelector('.fc-daygrid-event-dot') || document.createElement('span');
                dotEl.classList.add('fc-daygrid-event-dot');
                dotEl.style.borderRadius = '50%';
                dotEl.style.backgroundColor = info.event.backgroundColor;

                // Clear the inner HTML of the event element and append the dot
                info.el.innerHTML = '';
                info.el.appendChild(dotEl);
            }
        },
        dayCellDidMount: function (dayCell) {
            // Check if the day is in the past
            const currentDate = new Date();
            currentDate.setHours(0, 0, 0, 0); // Reset time part to compare only dates

            if (dayCell.date >= currentDate && !tabletCheck()) {
                // Attach right-click event listener only if the day is not in the past
                if (AppState.isUserStaffAdmin) {
                    dayCell.el.addEventListener('contextmenu', function (event) {
                        event.preventDefault();
                        handleCalendarRightClick(event, dayCell.date);
                    });
                }
            }
        },
    };
}

function displayEventList(events, date) {
    let eventListHtml = '<h4 style="font-size: 14px; font-weight: bold;">' + eventsOnTxt + ' ' + moment(date).format('MMMM Do, YYYY') + '</h4>';
    eventListHtml += '<hr>';

    events.forEach(function (event) {
        eventListHtml += `<div class="event-list-item-appt" data-event-id="${event.id}">${event.service_name}</div>`;
        eventListHtml += `<div><i class="fa fa-clock-o" aria-hidden="true"></i> ${moment(event.start_time).format('h:mm a')} - ${moment(event.end_time).format('h:mm a')}</div>`;
        eventListHtml += '<hr>';
    });

    const date_obj = new Date(date.toISOString())

    if (events.length === 0) {
        eventListHtml += `<div class="djangoAppt_no-events">` + noEventTxt + `</div>`;
    }

    eventListHtml += `<button class="btn btn-primary djangoAppt_btn-new-event" onclick="createNewAppointment('${date_obj}')">` + newEventTxt + `</button></div>`;

    const eventListContainer = document.getElementById('event-list-container');
    eventListContainer.innerHTML = eventListHtml;

    // Add click event listeners to each event item
    const eventItems = eventListContainer.getElementsByClassName('event-list-item-appt');
    for (let item of eventItems) {
        item.addEventListener('click', function () {
            const eventId = this.getAttribute('data-event-id');
            AppState.eventIdSelected = eventId;
            showEventModal(eventId, false, false).then(r => r);
        });
    }
}


function getHeaderToolbarConfig() {
    if (window.matchMedia('(max-width: 767px)').matches) {
        // Mobile configuration
        return {
            left: 'title', right: 'prev,next,dayGridMonth,timeGridDay'
        };
    } else if (window.matchMedia('(max-width: 991px)').matches) {
        // Tablet configuration
        return {
            left: 'prev,today,next', center: 'title', right: 'dayGridMonth,timeGridWeek,timeGridDay'
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
    if (window.innerWidth <= Constants.MOBILE_WIDTH_SMALL) return '400px';
    if (window.innerWidth <= Constants.MOBILE_WIDTH) return '450px';
    if (window.innerWidth <= Constants.SMALL_TABLET_WIDTH) return '600px';
    if (window.innerWidth <= Constants.TABLET_WIDTH) return '650px';
    if (window.innerWidth <= Constants.MEDIUM_WIDTH) return '767px';
    return '850px';
}

function setUserStaffAdminFlag() {
    return fetch(isUserStaffAdminURL)
        .then(response => response.json())
        .then(data => {
            if (data.is_staff_admin) {
                AppState.isUserStaffAdmin = true;
            } else {
                console.error(data.message || "Error fetching user details.");
                AppState.isUserStaffAdmin = false;
            }
        })
        .catch(error => {
            console.error("Error checking user's staff admin status: ", error);
            AppState.isUserStaffAdmin = false;
        });
}

function handleCalendarRightClick(event, date) {
    if (!AppState.isUserStaffAdmin) {
        showErrorModal(notStaffMemberTxt)
        return;
    }
    const contextMenu = document.getElementById("customContextMenu");
    contextMenu.style.top = `${event.pageY}px`;
    contextMenu.style.left = `${event.pageX}px`;
    contextMenu.style.display = 'block';

    const newAppointmentOption = document.getElementById("newAppointmentOption");
    newAppointmentOption.onclick = () => createNewAppointment(date);

    // Hide context menu on any click
    document.addEventListener('click', () => contextMenu.style.display = 'none', {once: true});
}

function goToEvent() {
    // Get the event URL
    const event = appointments.find(app => Number(app.id) === Number(AppState.eventIdSelected));
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
    AppStateProxy.isEditingAppointment = false;

    // Close the modal
    $('#eventDetailsModal').modal('hide');
}


// ################################################################ //
//                            Generic                               //
// ################################################################ //


async function cancelEdit() {
    // Retrieve the appointment that matches the eventIdSelected
    const appointment = appointments.find(app => Number(app.id) === Number(AppState.eventIdSelected));
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
    await showEventModal(appointment.id, false, false);
    toggleEditMode(); // Turn off edit mode
}

function confirmDeleteAppointment(appointmentId) {
    const deleteURL = deleteAppointmentURLTemplate
    const data = {appointment_id: appointmentId};

    fetch(deleteURL, {
        method: 'POST', headers: {
            'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCSRFToken(),
        }, body: JSON.stringify(data)
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            $('#eventDetailsModal').modal('hide');
            let event = AppState.calendar.getEventById(appointmentId);
            if (event) {
                event.remove();
            }
            showErrorModal(data.message, successTxt);
            closeConfirmModal();  // Close the confirmation modal

            // Remove the deleted appointment from the global appointments array
            appointments = appointments.filter(appointment => appointment.id !== appointmentId);

            // Refresh the event list for the current date
            const currentDate = AppState.calendar.getDate();
            const dateEvents = appointments
                .filter(event => moment(currentDate).isSame(event.start_time, 'day'))
                .sort((a, b) => new Date(a.start_time) - new Date(b.start_time));
            displayEventList(dateEvents, currentDate);
        })
        .catch(error => {
            console.error('Error:', error);
            showErrorModal(updateApptErrorTitleTxt);
        });
}

function deleteAppointment() {
    showModal(confirmDeletionTxt, confirmDeletionTxt, deleteBtnTxt, null, () => confirmDeleteAppointment(AppState.eventIdSelected));
}

function fetchServices(isEditMode = false) {
    let url = isEditMode && AppState.eventIdSelected ? `${fetchServiceListForStaffURL}?appointmentId=${AppState.eventIdSelected}` : fetchServiceListForStaffURL;
    return fetch(url)
        .then(response => response.json())
        .then(data => data.services_offered)
        .catch(error => console.error("Error fetching services: ", error));
}

function fetchStaffMembers(isEditMode = false) {
    let url = isEditMode && AppState.eventIdSelected ? `${fetchStaffListURL}?appointmentId=${AppState.eventIdSelected}` : fetchStaffListURL;
    return fetch(url)
        .then(response => response.json())
        .then(data => data.staff_members)
        .catch(error => console.error("Error fetching staff members: ", error));

}

async function populateServices(selectedServiceId, isEditMode = false) {
    const services = await fetchServices(isEditMode);
    if (!services) {
        showErrorModal(noServiceOfferedTxt)
    }
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

async function populateStaffMembers(selectedStaffId, isEditMode = false) {
    const staffMembers = await fetchStaffMembers(isEditMode);
    if (!staffMembers) {
        showErrorModal(noStaffMemberTxt)
    }
    const selectElement = document.createElement('select');
    staffMembers.forEach(staff => {
        const option = document.createElement('option');
        option.value = staff.id;  // Accessing the id
        option.textContent = staff.name;  // Accessing the name
        if (staff.id === selectedStaffId) {
            option.defaultSelected = true;
        }
        selectElement.appendChild(option);
    });
    return selectElement;
}

// Function to fetch services for a specific staff member
async function fetchServicesForStaffMember(staffId) {
    const url = `${fetchServiceListForStaffURL}?staff_member=${staffId}`;
    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error('Network response was not ok');
        const data = await response.json();
        return data.services_offered || [];
    } catch (error) {
        console.error("Error fetching services: ", error);
        return []; // Return an empty array in case of error
    }
}

// Function to update services dropdown options
function updateServicesDropdown(dropdown, services) {
    // Clear existing options
    dropdown.innerHTML = '';

    // Populate with new options
    services.forEach(service => {
        const option = new Option(service.name, service.id); // Assuming service object has id and name properties
        dropdown.add(option);
    });
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
        appointment_id: event.id, start_time: updatedStartTime, date: event.start.toISOString().split('T')[0]
    };

    try {
        const validationResponse = await fetch(validateApptDateURL, {
            method: 'POST', headers: {
                'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCSRFToken(),
            }, body: JSON.stringify(data)
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
        appointment_id: event.id, start_time: updatedStartTime, date: updatedDate,
    };

    try {
        const response = await fetch(updateApptDateURL, {
            method: 'POST', headers: {
                'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCSRFToken(),
            }, body: JSON.stringify(data)
        });

        const responseData = await response.json();
        if (response.ok) {
            showErrorModal(responseData.message, successTxt)
        } else {
            console.error('Failed to update appointment date. Server responded with:', response.statusText);
            showErrorModal(responseData.message, updateApptErrorTitleTxt);
            revertFunction();
        }
    } catch (error) {
        console.error('Failed to send data:', error);
        revertFunction();
    }
}

// ################################################################ //
//                      Create new Appt                             //
// ################################################################ //
function createNewAppointment(dateInput) {
    let date;
    if (typeof dateInput === 'string' || dateInput instanceof String) {
        date = new Date(dateInput);
    } else {
        date = dateInput;
    }

    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0'); // getMonth() returns 0-11
    const year = date.getFullYear();
    const formattedDate = `${year}-${month}-${day}`;
    const defaultStartTime = `${formattedDate}T09:00:00`;

    showCreateAppointmentModal(defaultStartTime, formattedDate).then(() => {
    });
}

async function showCreateAppointmentModal(defaultStartTime, formattedDate) {
    const servicesDropdown = await populateServices(null, false);
    let staffDropdown = null;
    if (isUserSuperUser) {
        staffDropdown = await populateStaffMembers(null, false);
        staffDropdown.id = "staffSelect";
        staffDropdown.disabled = false; // Enable dropdown
        attachEventListenersToDropdown(); // Attach event listener
    }
    servicesDropdown.id = "serviceSelect";
    servicesDropdown.disabled = false; // Enable dropdown

    document.getElementById('eventModalBody').innerHTML = prepareCreateAppointmentModalContent(servicesDropdown, staffDropdown, defaultStartTime, formattedDate);

    adjustCreateAppointmentModalButtons();
    AppStateProxy.isCreating = true;
    $('#eventDetailsModal').modal('show');
}

function adjustCreateAppointmentModalButtons() {
    document.getElementById("eventSubmitBtn").style.display = "";
    document.getElementById("eventCancelBtn").style.display = "none";
    document.getElementById("eventEditBtn").style.display = "none";
    document.getElementById("eventDeleteBtn").style.display = "none";
    document.getElementById("eventGoBtn").style.display = "none";
}

// ################################################################ //
//                      Show Event Modal                            //
// ################################################################ //

// Extract Appointment Data
async function getAppointmentData(eventId, isCreatingMode, defaultStartTime) {
    if (eventId && !isCreatingMode) {
        const appointment = appointments.find(app => Number(app.id) === Number(eventId));
        if (!appointment) {
            showErrorModal(apptNotFoundTxt, errorTxt);
            return null;
        }
        return appointment;
    }
    return {
        id: null,
        service_name: '',
        start_time: defaultStartTime,
        end_time: '',
        client_name: '',
        client_email: '',
        client_phone: '',
        client_address: '',
        additional_info: '',
        want_reminder: false,
        background_color: '',
        timezone: '',
    };
}

// Populate Services Dropdown
async function getServiceDropdown(serviceId, isEditMode) {
    const servicesDropdown = await populateServices(serviceId, !isEditMode);
    servicesDropdown.id = "serviceSelect";
    servicesDropdown.disabled = !isEditMode;
    return servicesDropdown;
}

// Populate Staff Dropdown
async function getStaffDropdown(staffId, isEditMode) {
    const staffDropdown = await populateStaffMembers(staffId, !isEditMode);
    staffDropdown.id = "staffSelect";
    staffDropdown.disabled = !isEditMode;
    return staffDropdown;
}

// Show Event Modal
async function showEventModal(eventId = null, isEditMode, isCreatingMode = false, defaultStartTime = '') {
    const appointment = await getAppointmentData(eventId, isCreatingMode, defaultStartTime);
    if (!appointment) return;

    const servicesDropdown = await getServiceDropdown(appointment.service_id, isEditMode);
    let staffDropdown = null;
    if (isUserSuperUser) {
        staffDropdown = await getStaffDropdown(appointment.staff_id, isEditMode);
        attachEventListenersToDropdown(); // Attach event listener
    }

    document.getElementById('eventModalBody').innerHTML = generateModalContent(appointment, servicesDropdown, isEditMode, staffDropdown);
    adjustModalButtonsVisibility(isEditMode, isCreatingMode);
    $('#eventDetailsModal').modal('show');
}

// Adjust Modal Buttons Visibility
function adjustModalButtonsVisibility(isEditMode, isCreatingMode) {
    const editButton = document.getElementById("eventEditBtn");
    const submitButton = document.getElementById("eventSubmitBtn");
    const deleteButton = document.getElementById("eventDeleteBtn");
    const goButton = document.getElementById("eventGoBtn");

    editButton.style.display = !isEditMode && !isCreatingMode ? "" : "none";
    submitButton.style.display = isCreatingMode || isEditMode ? "" : "none";
    deleteButton.style.display = !isEditMode && !isCreatingMode ? "" : "none";
    goButton.style.display = isCreatingMode ? "none" : "";
}

// ################################################################ //
//                         Edit Logic                               //
// ################################################################ //

function toggleEditMode() {
    const modal = document.getElementById("eventDetailsModal");
    const appointment = appointments.find(app => Number(app.id) === Number(AppState.eventIdSelected));
    AppStateProxy.isCreating = false; // Turn off creating mode

    // Proceed only if an appointment is found
    if (appointment) {
        AppStateProxy.isEditingAppointment = !AppState.isEditingAppointment;  // Toggle the editing state
        updateModalUIForEditMode(modal, AppState.isEditingAppointment);
    } else {
        console.error("Appointment not found!");
    }
}

function updateModalUIForEditMode(modal, isEditingAppointment) {
    const inputs = modal.querySelectorAll("input");
    const staffDropdown = document.getElementById("staffSelect");
    const servicesDropdown = document.getElementById("serviceSelect");
    const editButton = document.getElementById("eventEditBtn");
    const submitButton = document.getElementById("eventSubmitBtn");
    const closeButton = modal.querySelector(".btn-secondary[data-dismiss='modal']");
    const cancelButton = document.getElementById("eventCancelBtn");
    const deleteButton = document.getElementById("eventDeleteBtn");
    const goButton = document.getElementById("eventGoBtn");
    const endTimeLabel = modal.querySelector("label[for='endTime']");
    const endTimeInput = modal.querySelector("input[name='endTime']");

    // Toggle input and dropdown enable/disable state
    inputs.forEach(input => input.disabled = !isEditingAppointment);
    staffDropdown.disabled = !isEditingAppointment;
    servicesDropdown.disabled = !isEditingAppointment;

    // Toggle visibility of UI elements
    toggleElementVisibility(editButton, !isEditingAppointment);
    toggleElementVisibility(submitButton, isEditingAppointment);
    toggleElementVisibility(cancelButton, isEditingAppointment);
    toggleElementVisibility(deleteButton, !isEditingAppointment);
    toggleElementVisibility(closeButton, !isEditingAppointment);
    toggleElementVisibility(endTimeLabel, !isEditingAppointment);  // Show end time in view mode
    toggleElementVisibility(endTimeInput, !isEditingAppointment);  // Show end time in view mode
    toggleElementVisibility(goButton, !isEditingAppointment);
}

function toggleElementVisibility(element, isVisible) {
    if (element) {
        element.style.display = isVisible ? "" : "none";
    }
}

// ################################################################ //
//                         Submit Logic                             //
// ################################################################ //

async function submitChanges() {
    const modal = document.getElementById("eventDetailsModal");
    const formData = collectFormDataFromModal(modal);

    if (!validateFormData(formData)) return;

    const response = await sendAppointmentData(formData);
    if (response.ok) {
        const responseData = await response.json();
        if (AppState.isCreating) {
            addNewAppointmentToCalendar(responseData.appt[0]);
        } else {
            updateExistingAppointmentInCalendar(responseData.appt);
        }

        AppState.calendar.render();
    } else {
        const responseData = await response.json();
        showErrorModal(responseData.message);
    }
    closeModal();

}

// Collect form data from modal
function collectFormDataFromModal(modal) {
    const inputs = modal.querySelectorAll("input");
    const serviceId = modal.querySelector("#serviceSelect").value;
    let staffId = null;

    if (isUserSuperUser) {
        // If the user is a superuser, get the staff ID from the dropdown
        const staffDropdown = modal.querySelector("#staffSelect");
        if (staffDropdown) {
            staffId = staffDropdown.value;
        }
    }

    const data = {
        isCreating: AppState.isCreating,
        service_id: serviceId,
        appointment_id: AppState.eventIdSelected
    };

    if (staffId) {
        data.staff_member = staffId;
    }

    inputs.forEach(input => {
        if (input.name !== "date") {
            let key = input.name.replace(/([A-Z])/g, '_$1').toLowerCase();
            data[key] = input.value;
        }
    });

    if (AppState.isCreating) {
        data["date"] = modal.querySelector('input[name="date"]').value;
    }

    // Special handling for checkbox
    const wantReminderCheckbox = modal.querySelector('input[name="want_reminder"]');
    if (!wantReminderCheckbox.checked) {
        data['want_reminder'] = 'false';
    } else {
        data['want_reminder'] = 'true';
    }

    return data;
}

// Validate form data
function validateFormData(data) {
    return validateEmail(data["client_email"]);
}

// Validate email
function validateEmail(email) {
    const emailInput = document.querySelector('input[name="clientEmail"]');
    const emailError = document.getElementById("emailError");

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(emailInput.value)) {
        emailInput.style.border = "1px solid red";
        emailError.textContent = "Invalid email address, yeah.";
        emailError.style.color = "red";
        emailError.style.display = "inline";
        return false;
    } else {
        emailInput.style.border = "";
        emailError.textContent = "";
        emailError.style.display = "none";
        return true;
    }
}

// Send appointment data to server
async function sendAppointmentData(data) {
    const headers = {
        'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': getCSRFToken(),
    };

    return fetch(updateApptMinInfoURL, {
        method: 'POST', headers: headers, body: JSON.stringify(data)
    });
}

// Add new appointment to calendar
function addNewAppointmentToCalendar(newAppointment) {
    const newEvent = formatAppointmentsForCalendar([newAppointment])[0];
    appointments.push(newAppointment);
    AppState.calendar.addEvent(newEvent);
}

// Update existing appointment in calendar
function updateExistingAppointmentInCalendar(appointment) {
    let eventToUpdate = AppState.calendar.getEventById(AppState.eventIdSelected);
    if (eventToUpdate) {
        updateEventProperties(eventToUpdate, appointment);
    }
    // update appointment in appointments array
    const index = appointments.findIndex(app => Number(app.id) === Number(AppState.eventIdSelected));
    if (index !== -1) {
        appointments[index] = appointment;
    }
}

// Update event properties
function updateEventProperties(event, appointment) {
    event.setProp('title', appointment.service_name);
    event.setStart(moment(appointment.start_time).format('YYYY-MM-DDTHH:mm:ss'));
    event.setEnd(appointment.end_time);
    event.setExtendedProp('client_name', appointment.client_name);
    event.setProp('backgroundColor', appointment.background_color);
}
