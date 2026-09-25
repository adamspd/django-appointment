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
    $('#confirmModal').modal('show');
}


function closeConfirmModal() {
    $('#confirmModal').modal('hide');
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
