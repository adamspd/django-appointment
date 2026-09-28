// Add or edit a service (administration/manage_service.html): the tile next to the form shows the service as the
// service list will, and follows the fields as they change. The server formats the saved values; this is a preview.
document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('djappt-service-form');
    const preview = document.getElementById('djappt-service-preview');
    if (!form || !preview) {
        return;
    }

    const cover = preview.querySelector('.djappt-service-cover');
    let image = cover.querySelector('img');
    // The saved picture's element, swapped back in when the upload is undone (its address is never copied around)
    let savedImage = cover.classList.contains('djappt-service-cover--image') ? image : null;
    // A new upload is drawn here rather than loaded from a URL
    const uploadImage = document.createElement('canvas');
    let uploadCount = 0;
    const initial = cover.querySelector('.djappt-service-initial');
    const title = preview.querySelector('.djappt-service-title');
    const description = preview.querySelector('.djappt-service-desc');
    const duration = preview.querySelector('.djappt-service-duration');
    const price = preview.querySelector('.djappt-service-price');
    const locale = preview.dataset.locale || undefined;
    const field = (name) => form.elements.namedItem(name);

    function formatNumber(value, options) {
        try {
            return new Intl.NumberFormat(locale, options).format(value);
        } catch (e) {
            return new Intl.NumberFormat(undefined, options).format(value);
        }
    }

    // "01:30:00" (or "30:00") → "1 hour 30 minutes", in the page's language
    function formatDuration(value) {
        const parts = (value || '').trim().split(':').map(Number);
        if (parts.length < 2 || parts.length > 3 || parts.some(isNaN)) {
            return null;
        }
        const [hours, minutes] = parts.length === 3 ? parts : [0, parts[0]];
        const text = [];
        if (hours) text.push(formatNumber(hours, {style: 'unit', unit: 'hour', unitDisplay: 'long'}));
        if (minutes) text.push(formatNumber(minutes, {style: 'unit', unit: 'minute', unitDisplay: 'long'}));
        return text.join(' ');
    }

    function formatPrice(value, currency) {
        const amount = parseFloat(value);
        if (!amount) {
            return preview.dataset.freeText;
        }
        const whole = amount % 1 === 0;
        try {
            return formatNumber(amount, {
                style: 'currency', currency: currency || 'USD',
                minimumFractionDigits: whole ? 0 : 2, maximumFractionDigits: 2,
            });
        } catch (e) {
            return `${amount} ${currency}`;
        }
    }

    // Show a picture (an <img> or a <canvas>) in the cover, or the colour and the initial when there is none
    function showImage(picture) {
        if (picture && picture !== image) {
            image.replaceWith(picture);
            image = picture;
        }
        image.hidden = !picture;
        initial.hidden = !!picture;
        cover.classList.toggle('djappt-service-cover--image', !!picture);
    }

    function updateText() {
        const name = field('name') ? field('name').value.trim() : '';
        title.textContent = name;
        initial.textContent = name.charAt(0).toUpperCase();
        if (field('description')) {
            description.textContent = field('description').value.trim();
            description.style.display = description.textContent ? '' : 'none';
        }
        if (field('duration')) {
            const text = formatDuration(field('duration').value);
            if (text !== null) duration.textContent = text;
            duration.parentElement.style.display = duration.textContent ? '' : 'none';
        }
        if (field('price')) {
            price.textContent = formatPrice(field('price').value, field('currency') ? field('currency').value : '');
        }
        if (field('background_color')) {
            preview.style.setProperty('--djappt-service-color', field('background_color').value);
        }
    }

    function updateImage() {
        const input = field('image');
        const file = input && input.files && input.files[0];
        const count = ++uploadCount;
        if (file) {
            createImageBitmap(file).then((bitmap) => {
                if (count !== uploadCount) {
                    return;  // Another file was picked since
                }
                // No bigger than the tile needs, so a large photo doesn't hold a large canvas
                const scale = Math.min(1, 800 / bitmap.width);
                uploadImage.width = Math.round(bitmap.width * scale);
                uploadImage.height = Math.round(bitmap.height * scale);
                uploadImage.getContext('2d').drawImage(bitmap, 0, 0, uploadImage.width, uploadImage.height);
                bitmap.close();
                showImage(uploadImage);
            }).catch(() => {
                if (count === uploadCount) {
                    showImage(null);
                }
            });
            return;
        }
        const clear = field('image-clear');
        showImage(clear && clear.checked ? null : savedImage);
    }

    // An image that fails to load falls back to the colour and the initial, as on the service list
    const pageImage = image;
    pageImage.addEventListener('error', function () {
        savedImage = null;
        if (image === pageImage) {
            showImage(null);
        }
    });

    form.addEventListener('input', updateText);
    form.addEventListener('change', function (event) {
        if (event.target.name === 'image' || event.target.name === 'image-clear') {
            updateImage();
        } else {
            updateText();
        }
    });
    updateText();
});
