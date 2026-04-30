async function readJsonResponse(response) {
    const payload = await response.json();
    if (!response.ok) {
        throw new Error(payload.detail || 'Action impossible');
    }
    return payload;
}

export async function fetchAccount() {
    const response = await fetch('/api/account/me', { cache: 'no-store' });
    return readJsonResponse(response);
}

export async function submitAccountAuth(mode, email, password) {
    const response = await fetch(`/api/account/${mode}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
    });
    return readJsonResponse(response);
}

export async function saveAccountPreferences(prefs) {
    const response = await fetch('/api/account/preferences', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prefs }),
    });
    return readJsonResponse(response);
}

export async function logoutAccountSession() {
    const response = await fetch('/api/account/logout', { method: 'POST' });
    return readJsonResponse(response);
}
