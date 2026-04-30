export function getTzParts(tz) {
    const formatter = new Intl.DateTimeFormat('en-GB', {
        timeZone: tz,
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
    });

    return Object.fromEntries(formatter.formatToParts(new Date()).map((part) => [part.type, part.value]));
}

export function isMarketOpen(parts, market) {
    const nowMinutes = (Number(parts.hour) * 60) + Number(parts.minute);
    const openMinutes = (market.open[0] * 60) + market.open[1];
    const closeMinutes = (market.close[0] * 60) + market.close[1];
    return nowMinutes >= openMinutes && nowMinutes < closeMinutes;
}
