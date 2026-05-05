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

export async function confirmAccountEmail(email, code) {
    const response = await fetch('/api/account/confirm-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, code }),
    });
    return readJsonResponse(response);
}

export async function resendAccountConfirmation(email) {
    const response = await fetch('/api/account/resend-confirmation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
    });
    return readJsonResponse(response);
}

export async function logoutAccountSession() {
    const response = await fetch('/api/account/logout', { method: 'POST' });
    return readJsonResponse(response);
}


export async function createBillingPortalSession() {
    const response = await fetch('/api/billing/portal', { method: 'POST' });
    return readJsonResponse(response);
}

export async function syncBillingCheckoutSession(sessionId) {
    const response = await fetch('/api/billing/sync-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
    });
    return readJsonResponse(response);
}
