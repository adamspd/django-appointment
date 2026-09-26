// Service list (administration/service_list.html): show the services as cards or as a list. The choice is kept in
// this browser only; without JavaScript (or storage) the page shows cards.
document.addEventListener('DOMContentLoaded', function () {
    const grid = document.getElementById('djappt-service-grid');
    const switcher = document.querySelector('.djappt-view-switch');
    if (!grid || !switcher) {
        return;
    }

    const storageKey = 'djappt-service-view';
    const buttons = switcher.querySelectorAll('[data-view]');

    function show(view) {
        grid.classList.toggle('djappt-service-grid--list', view === 'list');
        buttons.forEach((button) => button.setAttribute('aria-pressed', String(button.dataset.view === view)));
    }

    let saved = null;
    try {
        saved = localStorage.getItem(storageKey);
    } catch (e) {
        // Storage blocked: stay on cards
    }
    show(saved === 'list' ? 'list' : 'cards');
    switcher.hidden = false;

    buttons.forEach((button) => button.addEventListener('click', function () {
        show(button.dataset.view);
        try {
            localStorage.setItem(storageKey, button.dataset.view);
        } catch (e) {
            // Storage blocked: the choice lasts until the page is left
        }
    }));
});
