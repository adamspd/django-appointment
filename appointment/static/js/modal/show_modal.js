function showModal(title, body, actionText, actionUrl, actionCallback) {
    // Set the content of the modal
    document.getElementById('modalLabel').innerText = title;
    document.getElementById('modalBody').innerText = body;
    const actionBtn = document.getElementById('modalActionBtn');
    actionBtn.innerText = actionText;

    // Determine the type of action: callback function or URL
    if (actionCallback) {
        actionBtn.onclick = () => {
            actionCallback();
            closeModal();  // Close the modal after action
        };
    } else if (actionUrl) {
        // Destructive actions only accept POST, so submit a form instead of following the link
        actionBtn.href = '#';
        actionBtn.onclick = (event) => {
            event.preventDefault();
            submitPostForm(actionUrl);
        };
    }

    // Display the modal
    bootstrap.Modal.getOrCreateInstance(document.getElementById('confirmModal')).show();
}


function closeConfirmModal() {
    bootstrap.Modal.getOrCreateInstance(document.getElementById('confirmModal')).hide();
}


function getConfirmModalCSRFToken() {
    const input = document.querySelector('input[name="csrfmiddlewaretoken"]');
    if (input) {
        return input.value;
    }
    const metaTag = document.querySelector('meta[name="csrf-token"]');
    if (metaTag) {
        return metaTag.getAttribute('content');
    }
    const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
}


function submitPostForm(url) {
    const form = document.createElement('form');
    form.method = 'post';
    form.action = url;
    const csrfInput = document.createElement('input');
    csrfInput.type = 'hidden';
    csrfInput.name = 'csrfmiddlewaretoken';
    csrfInput.value = getConfirmModalCSRFToken();
    form.appendChild(csrfInput);
    document.body.appendChild(form);
    form.submit();
}


// Declarative use, without inline JavaScript:
// <button type="button" data-djappt-confirm="{% url 'appointment:delete_service' service.id %}"
//         data-confirm-title="…" data-confirm-message="…" data-confirm-action="Delete">…</button>
// The modal then POSTs to the data-djappt-confirm URL.
document.addEventListener('click', function (event) {
    const trigger = event.target.closest('[data-djappt-confirm]');
    if (!trigger || !document.getElementById('confirmModal')) {
        return;
    }
    event.preventDefault();
    showModal(trigger.dataset.confirmTitle || '', trigger.dataset.confirmMessage || '',
        trigger.dataset.confirmAction || trigger.textContent.trim(), trigger.dataset.djapptConfirm, null);
});
