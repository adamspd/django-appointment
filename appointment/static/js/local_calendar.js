// Month view for languages whose calendar isn't Gregorian, like Persian (fa), which uses the Jalali calendar.
// FullCalendar already writes titles and day numbers in the language's calendar, but its month view always shows
// a Gregorian month. This view shows the language's month instead, using the browser's Intl to find where each
// month starts. Returns null when the language uses the Gregorian calendar, so nothing changes.
function localMonthCalendar(calendarLocale) {
    const months = localMonths(calendarLocale);
    if (!months) {
        return null;
    }
    const {isoDate, monthStart, nextMonthStart, previousMonthStart} = months;
    const moveMonths = (date, count) => {
        for (let i = 0; i < Math.abs(count); i++) {
            date = count > 0 ? nextMonthStart(date) : previousMonthStart(date);
        }
        return isoDate(date);
    };

    return {
        viewName: 'localMonth',
        view: {
            type: 'dayGrid',
            visibleRange: (current) => ({start: isoDate(monthStart(current)), end: isoDate(nextMonthStart(current))}),
            titleFormat: {year: 'numeric', month: 'long'},
            // Without this, FullCalendar writes the month name on the first day of each Gregorian month.
            monthStartFormat: {day: 'numeric'},
        },
        // The prev, next and year buttons move by Gregorian months, so in this view they move by local months.
        attach(calendar) {
            [['prev', -1], ['next', 1], ['prevYear', -12], ['nextYear', 12]].forEach(([method, months]) => {
                const original = calendar[method].bind(calendar);
                calendar[method] = () => calendar.view.type === 'localMonth'
                    ? calendar.gotoDate(moveMonths(calendar.getDate(), months)) : original();
            });
        },
    };
}

// Where the months of the language's calendar start, or null when it is the Gregorian calendar. Dates are read in
// UTC, like FullCalendar keeps them.
function localMonths(calendarLocale) {
    let system;
    try {
        system = new Intl.DateTimeFormat(calendarLocale || undefined).resolvedOptions().calendar;
    } catch (e) {
        return null;
    }
    if (!system || system === 'gregory') {
        return null;
    }
    const DAY = 24 * 60 * 60 * 1000;
    const parts = new Intl.DateTimeFormat('en-u-ca-' + system, {
        timeZone: 'UTC', year: 'numeric', month: 'numeric', day: 'numeric'});
    // {year, month, day} of a date in the language's calendar
    const localParts = (date) => Object.fromEntries(parts.formatToParts(date)
        .filter(part => ['year', 'month', 'day'].includes(part.type))
        .map(part => [part.type, parseInt(part.value, 10)]));
    const monthStart = (date) => new Date(date.getTime() - (localParts(date).day - 1) * DAY);
    const nextMonthStart = (date) => monthStart(new Date(monthStart(date).getTime() + 32 * DAY));
    const previousMonthStart = (date) => monthStart(new Date(monthStart(date).getTime() - DAY));
    return {DAY, localParts, monthStart, nextMonthStart, previousMonthStart,
        isoDate: (date) => date.toISOString().slice(0, 10)};
}

// The browser's date input only knows the Gregorian calendar. For a language with another calendar, like Persian,
// each <input type="date"> becomes day, month and year lists in that calendar, in the language's digits.
// The input stays in the form as a hidden field with the value the server reads (YYYY-MM-DD) and still sends
// change events. When a script sets its value or disables it, the lists follow.
function localDateTimeInputs(calendarLocale, root) {
    const months = localMonths(calendarLocale);
    if (!months) {
        return;
    }
    const {DAY, localParts, monthStart, nextMonthStart, isoDate} = months;
    const today = new Date(new Date().toISOString().slice(0, 10));
    // The months from 2 years back to 5 years ahead: [{year, month, start, days}]
    const allMonths = [];
    for (let start = monthStart(new Date(today.getTime() - 730 * DAY)); allMonths.length < 96;) {
        const next = nextMonthStart(start);
        allMonths.push({...localParts(start), start, days: Math.round((next - start) / DAY)});
        start = next;
    }
    const years = [...new Set(allMonths.map(m => m.year))];
    const number = new Intl.NumberFormat(calendarLocale, {useGrouping: false});
    const monthName = new Intl.DateTimeFormat(calendarLocale, {timeZone: 'UTC', month: 'long'});
    let fieldName = (field) => '';
    try {
        const names = new Intl.DisplayNames(calendarLocale, {type: 'dateTimeField'});
        fieldName = (field) => names.of(field);
    } catch (e) {
        // Older browsers: the lists are named after the field's label only
    }

    function list(field, width) {
        const select = document.createElement('select');
        select.className = 'form-select djappt-local-' + field;
        select.style.cssText = `flex: ${width} 1 0; min-width: 0;`;
        select.dataset.field = field;
        return select;
    }

    function fill(select, options, selected) {
        select.replaceChildren(new Option('', ''), ...options.map(([value, text]) => new Option(text, value)));
        select.value = selected === undefined ? '' : String(selected);
    }

    // Puts the lists in place of the input. show(value) shows a value in the lists and returns false when the
    // value isn't valid; read() shows the lists' choice again and returns its value, '' until it is complete.
    function replace(input, lists, show, read) {
        const label = input.id ? document.querySelector(`label[for="${CSS.escape(input.id)}"]`) : null;
        const name = label ? label.textContent.trim() : '';
        const box = document.createElement('div');
        box.style.cssText = 'display: flex; gap: .5rem; align-items: center;';
        lists.forEach((select) => {
            select.required = input.required;
            select.setAttribute('aria-label', [name, fieldName(select.dataset.field)].filter(Boolean).join(' – '));
            select.addEventListener('change', () => {
                const value = read();
                if (value !== input.value) {
                    shown = value;
                    input.value = value;
                    input.dispatchEvent(new Event('change', {bubbles: true}));
                }
            });
        });
        box.append(...lists);
        input.required = false;
        // A hidden field is never drawn, whatever a script does with its style
        input.type = 'hidden';
        input.after(box);
        if (label) {
            label.htmlFor = '';
            label.addEventListener('click', () => lists[0].focus());
        }

        let shown = null;
        function refresh() {
            lists.forEach(select => select.disabled = input.disabled);
            if (input.value === shown) {
                return;
            }
            // Like the browser's own inputs, a value they can't show is dropped
            shown = show(input.value) ? input.value : '';
            if (!shown) {
                show('');
                input.value = '';
            }
        }
        // The value and disabled attributes change when a script sets them on a hidden field
        new MutationObserver(refresh).observe(input, {attributes: true, attributeFilter: ['value', 'disabled']});
        refresh();
        return box;
    }

    function dateInput(input) {
        const [day, month, year] = [list('day', 2), list('month', 3), list('year', 3)];

        function showParts(dayValue, monthValue, yearValue) {
            fill(year, years.map(y => [y, number.format(y)]), yearValue);
            const yearMonths = allMonths.filter(m => m.year === yearValue);
            fill(month, yearMonths.map(m => [m.month, monthName.format(m.start)]), monthValue);
            const chosen = yearMonths.find(m => m.month === monthValue);
            const days = chosen ? chosen.days : 31;
            fill(day, Array.from({length: days}, (_, i) => [i + 1, number.format(i + 1)]),
                dayValue === undefined ? undefined : Math.min(dayValue, days));
        }

        replace(input, [day, month, year], (value) => {
            if (!value) {
                showParts(undefined, undefined, localParts(today).year);
                return true;
            }
            if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
                return false;
            }
            const parts = localParts(new Date(value));
            showParts(parts.day, parts.month, parts.year);
            return true;
        }, () => {
            const yearValue = parseInt(year.value, 10);
            const monthValue = parseInt(month.value, 10);
            showParts(parseInt(day.value, 10) || undefined, monthValue || undefined, yearValue);
            const chosen = allMonths.find(m => m.year === yearValue && m.month === monthValue);
            return chosen && day.value ? isoDate(new Date(chosen.start.getTime() + (day.value - 1) * DAY)) : '';
        });
        // Three lists need a full row
        const field = input.closest('.djappt-field');
        if (field) {
            field.classList.add('djappt-field--wide');
        }
    }

    (root || document).querySelectorAll('input[type="date"]').forEach(dateInput);
}
