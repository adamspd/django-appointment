document.addEventListener('DOMContentLoaded', function () {
    // Only the package's own messages: the host page can have alerts of its own.
    const messageElements = document.querySelectorAll('.djappt .alert-dismissible');
    setTimeout(function () {
        messageElements.forEach(function (element) {
            element.style.display = 'none';
        });
    }, 10000);
});
