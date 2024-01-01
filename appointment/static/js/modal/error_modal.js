let errorModalInstance = null;

function showErrorModal(message, title = errorTxt) {
    // Insert the error message into the modal
    document.getElementById('errorModalLabel').textContent = title;
    document.getElementById('errorModalMessage').textContent = message;

    // Show the modal
    if (!errorModalInstance) {
        errorModalInstance = new bootstrap.Modal(document.getElementById('errorModal'));
    }
    errorModalInstance.show();
}

function closeErrorModal() {
    if (errorModalInstance) {
        errorModalInstance.hide();
    }
}