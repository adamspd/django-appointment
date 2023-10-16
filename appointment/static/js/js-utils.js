document.addEventListener('DOMContentLoaded', function () {
    const messageElements = document.querySelectorAll('.alert-dismissible');
    setTimeout(function () {
        messageElements.forEach(function (element) {
            element.style.display = 'none';
        });
    }, 5000);
});
