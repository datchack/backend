export function loadStoredPrefs(key) {
    try {
        return JSON.parse(localStorage.getItem(key)) || {};
    } catch {
        return {};
    }
}

export function writeStoredPrefs(key, prefs) {
    localStorage.setItem(key, JSON.stringify(prefs || {}));
}

export function mergeStoredPrefs(key, patch) {
    const current = loadStoredPrefs(key);
    const next = { ...current, ...(patch || {}) };
    writeStoredPrefs(key, next);
    return next;
}
