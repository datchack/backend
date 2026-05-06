let resetLang = localStorage.getItem('xt_lang') || 'fr';

const RESET_COPY = {
    fr: {
        meta_title: 'Réinitialiser le mot de passe - XAUTERMINAL',
        back_landing: 'Retour landing',
        kicker: 'SÉCURITÉ DU COMPTE',
        title: 'Choisis un nouveau mot de passe',
        copy: 'Entre un nouveau mot de passe pour ton compte XAUTERMINAL. Le lien envoyé par email expire automatiquement.',
        new_password: 'Nouveau mot de passe',
        confirm_password: 'Confirmer le mot de passe',
        submit: 'Mettre à jour le mot de passe',
        missing_token: 'Lien de réinitialisation manquant ou invalide.',
        mismatch: 'Les deux mots de passe ne correspondent pas.',
        short: 'Le mot de passe doit contenir au moins 8 caractères.',
        loading: 'Mise à jour du mot de passe...',
        success: 'Mot de passe mis à jour. Tu peux maintenant te connecter.',
        error: 'Impossible de modifier le mot de passe.',
    },
    en: {
        meta_title: 'Reset password - XAUTERMINAL',
        back_landing: 'Back to landing',
        kicker: 'ACCOUNT SECURITY',
        title: 'Choose a new password',
        copy: 'Enter a new password for your XAUTERMINAL account. The email link expires automatically.',
        new_password: 'New password',
        confirm_password: 'Confirm password',
        submit: 'Update password',
        missing_token: 'Missing or invalid reset link.',
        mismatch: 'Both passwords must match.',
        short: 'Password must contain at least 8 characters.',
        loading: 'Updating password...',
        success: 'Password updated. You can now log in.',
        error: 'Unable to update password.',
    },
};

function t(key) {
    return RESET_COPY[resetLang]?.[key] || RESET_COPY.fr[key] || key;
}

function applyResetLanguage() {
    document.documentElement.lang = resetLang;
    document.querySelectorAll('[data-i18n]').forEach((el) => {
        el.textContent = t(el.dataset.i18n);
    });
    const title = document.querySelector('title');
    if (title?.dataset.i18n) title.textContent = t(title.dataset.i18n);
    const toggle = document.querySelector('[data-reset-lang-toggle]');
    if (toggle) toggle.textContent = resetLang === 'fr' ? 'EN' : 'FR';
}

function setResetMessage(message, tone = '') {
    const el = document.getElementById('reset-password-message');
    if (!el) return;
    el.textContent = message;
    el.className = `account-message${tone ? ` ${tone}` : ''}`;
}

async function submitReset(event) {
    event.preventDefault();
    const token = new URLSearchParams(window.location.search).get('token') || '';
    const password = document.getElementById('reset-password-new')?.value || '';
    const confirm = document.getElementById('reset-password-confirm')?.value || '';
    if (!token) {
        setResetMessage(t('missing_token'), 'err');
        return;
    }
    if (password.length < 8) {
        setResetMessage(t('short'), 'err');
        return;
    }
    if (password !== confirm) {
        setResetMessage(t('mismatch'), 'err');
        return;
    }

    try {
        setResetMessage(t('loading'));
        const response = await fetch('/api/account/password-reset/confirm', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token, new_password: password }),
        });
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || t('error'));
        document.getElementById('reset-password-form')?.reset();
        setResetMessage(payload.message || t('success'), 'ok');
        window.setTimeout(() => {
            window.location.href = '/';
        }, 1600);
    } catch (error) {
        setResetMessage(error.message || t('error'), 'err');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    applyResetLanguage();
    document.querySelector('[data-reset-lang-toggle]')?.addEventListener('click', () => {
        resetLang = resetLang === 'fr' ? 'en' : 'fr';
        localStorage.setItem('xt_lang', resetLang);
        applyResetLanguage();
    });
    document.getElementById('reset-password-form')?.addEventListener('submit', submitReset);
    if (!new URLSearchParams(window.location.search).get('token')) {
        setResetMessage(t('missing_token'), 'err');
    }
});
