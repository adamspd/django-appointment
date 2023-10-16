function showModal(title, body, actionText, actionUrl) {
    // Set the content of the modal
    document.getElementById('modalLabel').innerText = title;
    document.getElementById('modalBody').innerText = body;
    const actionBtn = document.getElementById('modalActionBtn');
    actionBtn.innerText = actionText;
    actionBtn.setAttribute('href', actionUrl);

    // Display the modal
    $('#confirmModal').modal('show');
}

function closeModal() {
    $('#confirmModal').modal('hide');
}