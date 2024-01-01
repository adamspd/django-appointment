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
        actionBtn.href = actionUrl;
    }

    // Display the modal
    $('#confirmModal').modal('show');
}


function closeConfirmModal() {
    $('#confirmModal').modal('hide');
}