document.addEventListener('DOMContentLoaded', function() {
    const isRecurringCheckbox = document.getElementById('id_is_recurring');
    const recurrenceFieldsDiv = document.getElementById('recurrence_rule_fields');
    const frequencySelect = document.getElementById('recurrence_frequency');
    const weeklyDaySelection = document.getElementById('weekly_day_selection');
    const dayButtons = document.querySelectorAll('.day-button');
    const endDateInput = document.getElementById('id_end_recurrence');
    const rruleInput = document.getElementById('id_recurrence_rule');
    const previewText = document.getElementById('recurring_preview_text');

    // Make revalidation function globally available
    window.revalidateSubmitButton = function() {
        return validateRecurringSettings();
    };

    // Sync form data with hidden fields
    function syncFormData() {
        const hiddenIsRecurring = document.getElementById('hidden_is_recurring');
        const hiddenEndRecurrence = document.getElementById('hidden_end_recurrence');

        if (hiddenIsRecurring) {
            hiddenIsRecurring.value = isRecurringCheckbox.checked ? 'true' : 'false';
        }

        if (hiddenEndRecurrence && endDateInput) {
            hiddenEndRecurrence.value = endDateInput.value;
        }
    }

    // Get the selected appointment date from the calendar or date display
    function getSelectedAppointmentDate() {
        // Try to get from global variable first
        if (window.selectedDate) {
            return new Date(window.selectedDate);
        }

        // Try to get from selected calendar cell
        const selectedCell = document.querySelector('.selected-cell');
        if (selectedCell && selectedCell.getAttribute('data-date')) {
            return new Date(selectedCell.getAttribute('data-date'));
        }

        // Fallback to today
        return new Date();
    }

    // Set date constraints for the until field based on selected appointment date
    function setDateConstraints() {
        const appointmentDate = getSelectedAppointmentDate();
        const maxDate = new Date(appointmentDate);
        maxDate.setMonth(appointmentDate.getMonth() + maxRecurringMonths);

        // Format dates for input[type="date"]
        const appointmentDateStr = appointmentDate.toISOString().split('T')[0];
        const maxDateStr = maxDate.toISOString().split('T')[0];

        endDateInput.setAttribute('min', appointmentDateStr);
        endDateInput.setAttribute('max', maxDateStr);
    }

    // Auto-set until date when recurring is enabled
    function autoSetUntilDate() {
        if (isRecurringCheckbox.checked && !endDateInput.value) {
            const appointmentDate = getSelectedAppointmentDate();
            // Set until date to same date as appointment (user can change it)
            endDateInput.value = appointmentDate.toISOString().split('T')[0];
            updateRecurrenceRule();
        }
    }

    // Update until date when calendar selection changes (even if field has value)
    function updateUntilDateToMatch() {
        if (isRecurringCheckbox.checked) {
            const appointmentDate = getSelectedAppointmentDate();
            // Always update to match the selected appointment date
            endDateInput.value = appointmentDate.toISOString().split('T')[0];
            updateRecurrenceRule();
            syncFormData();
        }
    }

    // Validate end date input
    function validateEndDate() {
        const selectedDate = new Date(endDateInput.value);
        const appointmentDate = getSelectedAppointmentDate();
        appointmentDate.setHours(0, 0, 0, 0);

        const maxDate = new Date(appointmentDate);
        maxDate.setMonth(appointmentDate.getMonth() + maxRecurringMonths);
        maxDate.setHours(23, 59, 59, 999);

        if (selectedDate < appointmentDate) {
            alert('End date cannot be before the appointment date.');
            endDateInput.value = '';
            return false;
        }

        if (selectedDate > maxDate) {
            alert(`End date cannot be more than ${maxRecurringMonths} months from the appointment date.`);
            endDateInput.value = '';
            return false;
        }

        return true;
    }

    // Make calendar sync function globally available
    window.syncRecurringWithCalendarSelection = function() {
        if (!document.getElementById('id_is_recurring').checked ||
            document.getElementById('recurrence_frequency').value !== 'WEEKLY') {
            // Still update the until date even if not weekly recurring
            updateUntilDateToMatch();
            return;
        }

        let dateStr = null;

        // Method 1: Use global selectedDate variable
        if (window.selectedDate) {
            dateStr = window.selectedDate;
        }

        // Method 2: Find selected cell and get its data-date
        if (!dateStr) {
            const selectedCell = document.querySelector('.selected-cell');
            if (selectedCell) {
                dateStr = selectedCell.getAttribute('data-date');
            }
        }

        if (dateStr) {
            const date = new Date(dateStr);
            const dayOfWeek = date.getDay();
            const dayMapping = ['SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA'];
            const dayCode = dayMapping[dayOfWeek];

            // Clear existing selections
            document.querySelectorAll('.day-button').forEach(btn => btn.classList.remove('selected'));

            // Select the matching day
            const dayButton = document.querySelector(`.day-button[data-day="${dayCode}"]`);
            if (dayButton) {
                dayButton.classList.add('selected');
                updateRecurrenceRule();
            }
        }

        // Update date constraints and until date when calendar selection changes
        setDateConstraints();
        updateUntilDateToMatch();
    };

    function updateRecurrenceRule() {
        const frequency = frequencySelect.value;
        let rrule = `RRULE:FREQ=${frequency}`;

        if (frequency === 'WEEKLY') {
            const selectedDays = Array.from(document.querySelectorAll('.day-button.selected'))
                .map(btn => btn.dataset.day);
            if (selectedDays.length > 0) {
                rrule += `;BYDAY=${selectedDays.join(',')}`;
            }
        }

        if (endDateInput.value) {
            const endDate = new Date(endDateInput.value);
            endDate.setHours(23, 59, 59, 999);
            rrule += `;UNTIL=${endDate.toISOString().replace(/[-:]/g, '').split('.')[0]}Z`;
        }

        rruleInput.value = rrule;
        updatePreview();
    }

    function updatePreview() {
        const frequency = frequencySelect.value;
        const endDate = endDateInput.value;
        let previewHtml = '';

        if (frequency === 'WEEKLY') {
            const selectedDays = Array.from(document.querySelectorAll('.day-button.selected'));
            if (selectedDays.length > 0) {
                const dayNames = selectedDays.map(btn => {
                    const day = btn.dataset.day;
                    const names = {MO:'Monday', TU:'Tuesday', WE:'Wednesday', TH:'Thursday', FR:'Friday', SA:'Saturday', SU:'Sunday'};
                    return names[day];
                });
                previewHtml = `Every week on ${dayNames.join(', ')}`;
            } else {
                previewHtml = 'Select days for weekly recurrence';
            }
        } else if (frequency === 'DAILY') {
            previewHtml = 'Every day';
        } else if (frequency === 'MONTHLY') {
            previewHtml = 'Every month';
        }

        if (endDate && previewHtml) {
            // Format date as "Month Day, Year" (e.g., "June 11th, 2025")
            const endDateObj = new Date(endDate);
            const formattedEndDate = endDateObj.toLocaleDateString('en-US', {
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });

            // Add ordinal suffix (st, nd, rd, th)
            const day = endDateObj.getDate();
            const ordinalSuffix = getOrdinalSuffix(day);
            const finalFormattedDate = formattedEndDate.replace(/(\d+)/, `$1${ordinalSuffix}`);

            previewHtml += ` until ${finalFormattedDate}`;
        }

        const finalPreviewText = previewHtml || 'Configure settings';

        // Update the main preview text
        previewText.textContent = finalPreviewText;

        // Update or create the service description preview
        updateServiceDescriptionPreview(finalPreviewText);
    }

    // Helper function to get ordinal suffix (st, nd, rd, th)
    function getOrdinalSuffix(day) {
        if (day > 3 && day < 21) return 'th';
        switch (day % 10) {
            case 1: return 'st';
            case 2: return 'nd';
            case 3: return 'rd';
            default: return 'th';
        }
    }

    // Function to manage the recurring preview in service description
    function updateServiceDescriptionPreview(previewText) {
        const serviceDescriptionContent = document.querySelector('.djangoAppt_service-description-content');
        const serviceDateTime = document.getElementById('service-datetime-chosen');

        if (!serviceDescriptionContent || !serviceDateTime) return;

        // Look for existing recurring preview element
        let recurringPreview = serviceDescriptionContent.querySelector('.service-recurring-preview');

        if (isRecurringCheckbox.checked && previewText && previewText !== 'Configure settings') {
            if (!recurringPreview) {
                // Create new recurring preview element
                recurringPreview = document.createElement('p');
                recurringPreview.className = 'service-recurring-preview';
                recurringPreview.style.fontSize = '0.8em';
                recurringPreview.style.color = '#888';
                recurringPreview.style.fontStyle = 'italic';
                recurringPreview.style.margin = '-12px 0 12px 0';
                recurringPreview.style.lineHeight = '1.2';

                // Insert after service-datetime-chosen
                serviceDateTime.parentNode.insertBefore(recurringPreview, serviceDateTime.nextSibling);
            }
            recurringPreview.textContent = previewText;
        } else if (recurringPreview) {
            // Remove the preview if recurring is disabled or no valid preview
            recurringPreview.remove();
        }
    }

    // Validate recurring settings and update submit button state
    function validateRecurringSettings() {
        const submitButton = document.querySelector('.btn-submit-appointment');

        if (isRecurringCheckbox.checked) {
            // If recurring is enabled, end date is required
            const hasEndDate = endDateInput.value && endDateInput.value.trim() !== '';

            if (!hasEndDate) {
                submitButton.disabled = true;
                submitButton.title = 'End date is required for recurring appointments';
                return false;
            }

            // If weekly, at least one day must be selected
            if (frequencySelect.value === 'WEEKLY') {
                const selectedDays = document.querySelectorAll('.day-button.selected');
                if (selectedDays.length === 0) {
                    submitButton.disabled = true;
                    submitButton.title = 'Select at least one day for weekly recurring appointments';
                    return false;
                }
            }
        }

        // Check if a time slot is selected
        const hasSelectedSlot = document.querySelector('.djangoAppt_appointment-slot.selected');
        if (hasSelectedSlot) {
            submitButton.disabled = false;
            submitButton.title = '';
        }

        return true;
    }

    // Toggle recurring settings visibility
    if (isRecurringCheckbox && recurrenceFieldsDiv) {
        isRecurringCheckbox.addEventListener('change', function() {
            recurrenceFieldsDiv.style.display = this.checked ? 'block' : 'none';
            if (this.checked && frequencySelect.value === 'WEEKLY') {
                setTimeout(() => window.syncRecurringWithCalendarSelection(), 100);
            } else if (this.checked) {
                // Update until date even for non-weekly recurring
                setTimeout(() => updateUntilDateToMatch(), 100);
            } else {
                rruleInput.value = '';
            }

            // Update constraints when enabling recurring
            setDateConstraints();

            // Update the service description preview when toggling recurring
            updateServiceDescriptionPreview('');

            syncFormData();
            validateRecurringSettings();
        });
    }

    // Handle frequency changes
    frequencySelect.addEventListener('change', function() {
        weeklyDaySelection.style.display = this.value === 'WEEKLY' ? 'block' : 'none';
        if (this.value === 'WEEKLY') {
            setTimeout(() => window.syncRecurringWithCalendarSelection(), 100);
        } else {
            // For non-weekly frequencies, still update the until date
            updateUntilDateToMatch();
        }
        updateRecurrenceRule();
        validateRecurringSettings();
    });

    // Handle day button clicks
    dayButtons.forEach(button => {
        button.addEventListener('click', function() {
            this.classList.toggle('selected');
            updateRecurrenceRule();
            validateRecurringSettings();
        });
    });

    // Handle end date changes
    endDateInput.addEventListener('change', function() {
        if (validateEndDate()) {
            updateRecurrenceRule();
            syncFormData();
            validateRecurringSettings();
        }
    });

    // Initialize
    weeklyDaySelection.style.display = frequencySelect.value === 'WEEKLY' ? 'block' : 'none';
    setDateConstraints();
    syncFormData();
});
