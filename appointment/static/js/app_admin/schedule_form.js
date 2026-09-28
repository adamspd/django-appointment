// Working hours, day off and unavailability forms (administration/manage_*.html).
// The fields are the browser's own date and time pickers. Before sending, each field marked data-raw-target copies
// its value, in the format the server reads, into its hidden *_raw field. The form is sent in the background; the
// server answers with JSON: the page to go to next, or a message shown in the error modal.
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

    form.addEventListener('submit', async function (event) {
        event.preventDefault();
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
            showErrorModal(data.message || response.statusText);
        } catch (error) {
            showErrorModal(error.message);
        }
        button.disabled = false;
    });
});
