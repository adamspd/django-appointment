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
