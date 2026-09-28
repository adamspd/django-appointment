// Working hours, day off and unavailability forms (administration/manage_*.html).
// The fields are the browser's own date and time pickers, named like the model fields; they send ISO values
// (YYYY-MM-DD, HH:MM), which the server reads as they are. The form is sent in the background; the server answers
// with JSON: the page to go to next, or the errors of each field ({"errors": {"end_time": ["..."]}}), shown under
// the fields. An error that belongs to no field on the page goes to the error modal.
// Templates written before 3.13 may still mark fields with data-raw-target; their *_raw copies are filled as before.
document.addEventListener('DOMContentLoaded', function () {
    const form = document.querySelector('form[data-schedule-form]');
    if (!form) {
        return;
    }

    // "09:30" → "09:30:00"; a time input may already include the seconds
    const withSeconds = (value) => (value.length === 5 ? `${value}:00` : value);

    const formats = {
        date: (value) => value,
        time: (value) => withSeconds(value),
        // Working hours: a full date-time, of which the server only keeps the time
        datetime: (value) => `1970-01-01T${withSeconds(value)}`,
    };

    function fillRawFields() {
        form.querySelectorAll('[data-raw-target]').forEach((input) => {
            const raw = document.getElementById(input.dataset.rawTarget);
            const format = formats[input.dataset.rawFormat] || formats.date;
            raw.value = input.value ? format(input.value) : '';
        });
    }

    // An end date can't be before the start date
    const startDate = form.querySelector('[data-start-date]');
    const endDate = form.querySelector('[data-end-date]');
    if (startDate && endDate) {
        const syncEnd = () => {
            endDate.min = startDate.value;
            if (startDate.value && (!endDate.value || endDate.value < startDate.value)) {
                endDate.value = startDate.value;
            }
        };
        startDate.addEventListener('change', syncEnd);
        syncEnd();
    }

    function clearFieldErrors() {
        form.querySelectorAll('.djappt-field-error[data-schedule-error]').forEach((el) => el.remove());
        form.querySelectorAll('.is-invalid').forEach((el) => {
            el.classList.remove('is-invalid');
            el.removeAttribute('aria-invalid');
        });
    }

    // Returns the messages that have no field on the page
    function showFieldErrors(errors) {
        const unplaced = [];
        Object.entries(errors || {}).forEach(([name, messages]) => {
            const inputs = form.querySelectorAll(`[name="${CSS.escape(name)}"]`);
            if (!inputs.length) {
                unplaced.push(...messages);
                return;
            }
            inputs.forEach((input) => {
                input.classList.add('is-invalid');
                input.setAttribute('aria-invalid', 'true');
            });
            const field = inputs[0].closest('.djappt-field') || inputs[0].parentElement;
            messages.forEach((message) => {
                const error = document.createElement('div');
                error.className = 'djappt-field-error';
                error.dataset.scheduleError = '';
                error.textContent = message;
                field.appendChild(error);
            });
        });
        return unplaced;
    }

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
        clearFieldErrors();
        fillRawFields();
        const button = form.querySelector('[type="submit"]');
        button.disabled = true;
        try {
            const response = await fetch(form.dataset.postUrl || window.location.href, {
                method: 'POST',
                body: new FormData(form),
                headers: {'X-Requested-With': 'XMLHttpRequest'},
            });
            const data = await response.json().catch(() => ({}));
            if (response.ok && data.success && data.redirect_url) {
                window.location.href = data.redirect_url;
                return;
            }
            if (data.errors) {
                const unplaced = showFieldErrors(data.errors);
                if (unplaced.length) {
                    showErrorModal(unplaced.join(' '));
                }
            } else {
                showErrorModal(data.message || response.statusText);
            }
        } catch (error) {
            showErrorModal(error.message);
        }
        button.disabled = false;
    });
});
