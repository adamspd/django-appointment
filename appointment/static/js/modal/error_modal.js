let errorModalInstance = null;

function showErrorModal(message, title = errorTxt) {
    // Insert the error message into the modal
    document.getElementById('errorModalLabel').textContent = title;
    document.getElementById('errorModalMessage').textContent = message;

    // Show the modal
    if (!errorModalInstance) {
        const element = document.getElementById('errorModal');
        errorModalInstance = new bootstrap.Modal(element);
        // Shown over another modal (a form): once closed, that one is still open, so keep the page from scrolling
        element.addEventListener('hidden.bs.modal', function () {
            if (document.querySelector('.modal.show')) {
                document.body.classList.add('modal-open');
            }
        });
    }
    errorModalInstance.show();
}

function closeErrorModal() {
    if (errorModalInstance) {
        errorModalInstance.hide();
    }
}