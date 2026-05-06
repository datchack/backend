const state = {
    account: null,
};
let accountLang = localStorage.getItem('xt_lang') || 'fr';

const ACCOUNT_COPY = {
    fr: {
        meta_title: 'Mon compte - XAUTERMINAL',
        nav_pricing: 'Formules',
        nav_terminal: 'Terminal',
        nav_logout: 'Déconnexion',
        hero_kicker: 'ESPACE PERSONNEL',
        hero_title: 'Mon compte XAUTERMINAL',
        hero_copy: 'Gère ton profil, ton accès au terminal, ta sécurité et ton abonnement depuis un espace dédié.',
        back_landing: 'Retour landing',
        open_terminal: 'Ouvrir le terminal',
        login_required_kicker: 'CONNEXION REQUISE',
        login_required_title: 'Connecte-toi pour accéder à ton espace compte.',
        login_required_copy: 'Depuis la landing, ouvre la connexion. Une fois connecté, le bouton Connexion devient Mon compte.',
        status_kicker: 'STATUT',
        loading: 'Chargement...',
        status_loading_copy: 'Vérification de ton accès.',
        terminal_access: 'Accès terminal',
        period_end: 'Échéance',
        resend_code: 'Renvoyer le code',
        manage_stripe: 'Gérer avec Stripe',
        billing_kicker: 'ABONNEMENT',
        billing_title: 'Formule et facturation',
        billing_default_copy: 'Stripe gère les moyens de paiement, factures, changements de formule et annulations.',
        billing_status: 'Statut',
        stripe_customer: 'Client Stripe',
        subscription: 'Abonnement',
        price: 'Prix',
        monthly: 'Mensuel',
        yearly: 'Annuel',
        lifetime_plan: 'Lifetime',
        admin_kicker: 'ADMINISTRATION',
        admin_title: 'Panel admin',
        admin_copy: 'Accède à la gestion des utilisateurs, des accès et des statuts de compte depuis ton espace owner.',
        open_admin: 'Ouvrir le panel admin',
        profile_kicker: 'PROFIL',
        profile_title: 'Informations personnelles',
        first_name: 'Prénom',
        last_name: 'Nom',
        address: 'Adresse',
        postal_code: 'Code postal',
        city: 'Ville',
        country: 'Pays',
        save_profile: 'Enregistrer le profil',
        security_kicker: 'SÉCURITÉ',
        password_title: 'Mot de passe',
        current_password: 'Mot de passe actuel',
        new_password: 'Nouveau mot de passe',
        update_password: 'Mettre à jour',
        owner: 'OWNER',
        active: 'ACTIF',
        monthly_plan: 'MENSUEL',
        yearly_plan: 'ANNUEL',
        lifetime: 'LIFETIME',
        trial: 'ESSAI',
        past_due: 'PAIEMENT EN RETARD',
        canceled: 'ANNULÉ',
        email_to_confirm: 'EMAIL À CONFIRMER',
        payment_required: 'PAIEMENT REQUIS',
        inactive: 'INACTIF',
        owner_account: 'Compte owner',
        email_unconfirmed: 'Email non confirmé',
        active_stripe: 'Actif via Stripe',
        stripe_linked: 'Stripe lié',
        waiting_payment: 'En attente de paiement',
        stripe_unlinked: 'Non lié à Stripe',
        status_active_title: 'Accès terminal actif',
        status_payment_title: 'Paiement Stripe requis',
        status_confirm_title: 'Email à confirmer',
        status_active_copy: 'Ton compte peut ouvrir le terminal complet. La facturation reste gérable depuis Stripe.',
        status_payment_copy: 'Ton email est confirmé. Choisis une formule pour démarrer ton essai et lier Stripe au compte.',
        status_confirm_copy: 'Confirme ton adresse email avant de choisir une formule Stripe.',
        billing_active_copy: 'Ton abonnement est lié à Stripe. Tu peux gérer tes factures, moyens de paiement, changements de formule et annulations depuis le portail Stripe.',
        billing_ready_copy: 'Ton email est confirmé. Choisis une formule pour démarrer ton essai et lier automatiquement Stripe à ton compte XAUTERMINAL.',
        billing_confirm_copy: 'Confirme ton email avant de choisir une formule. Stripe gérera ensuite les moyens de paiement, factures et annulations.',
        stripe_portal_ready: 'Ouvrir le portail Stripe',
        stripe_portal_missing: 'Un paiement Stripe doit être lié au compte avant d’ouvrir le portail',
        choose_plan_ready: 'Choisir cette formule via Stripe',
        choose_plan_missing: 'Confirme ton email avant de choisir une formule',
        saving: 'Enregistrement...',
        profile_saved: 'Profil enregistré.',
        profile_error: "Impossible d'enregistrer le profil.",
        updating: 'Mise à jour...',
        password_saved: 'Mot de passe mis à jour.',
        password_error: 'Mot de passe non modifié.',
        redirect_stripe: 'Redirection vers Stripe...',
        payment_unavailable: 'Paiement indisponible.',
        opening_portal: 'Ouverture du portail Stripe...',
        portal_unavailable: 'Portail Stripe indisponible.',
        sending_code: 'Envoi du code...',
        code_sent: 'Code de confirmation renvoyé par email.',
        code_error: 'Code non envoyé.',
        payment_canceled: 'Paiement annulé. Tu peux choisir une formule quand tu veux.',
        validating_payment: 'Validation du paiement Stripe...',
        payment_valid: 'Paiement validé. Ton accès est activé.',
        payment_pending: 'Paiement reçu, synchronisation en attente.',
    },
    en: {
        meta_title: 'My account - XAUTERMINAL',
        nav_pricing: 'Plans',
        nav_terminal: 'Terminal',
        nav_logout: 'Logout',
        hero_kicker: 'PERSONAL SPACE',
        hero_title: 'My XAUTERMINAL Account',
        hero_copy: 'Manage your profile, terminal access, security and subscription from one dedicated space.',
        back_landing: 'Back to landing',
        open_terminal: 'Open terminal',
        login_required_kicker: 'LOGIN REQUIRED',
        login_required_title: 'Log in to access your account space.',
        login_required_copy: 'Open login from the landing page. Once connected, the Login button becomes My account.',
        status_kicker: 'STATUS',
        loading: 'Loading...',
        status_loading_copy: 'Checking your access.',
        terminal_access: 'Terminal access',
        period_end: 'Period end',
        resend_code: 'Resend code',
        manage_stripe: 'Manage with Stripe',
        billing_kicker: 'SUBSCRIPTION',
        billing_title: 'Plan and billing',
        billing_default_copy: 'Stripe manages payment methods, invoices, plan changes and cancellations.',
        billing_status: 'Status',
        stripe_customer: 'Stripe customer',
        subscription: 'Subscription',
        price: 'Price',
        monthly: 'Monthly',
        yearly: 'Yearly',
        lifetime_plan: 'Lifetime',
        admin_kicker: 'ADMINISTRATION',
        admin_title: 'Admin panel',
        admin_copy: 'Access user, access and account status management from your owner space.',
        open_admin: 'Open admin panel',
        profile_kicker: 'PROFILE',
        profile_title: 'Personal information',
        first_name: 'First name',
        last_name: 'Last name',
        address: 'Address',
        postal_code: 'Postal code',
        city: 'City',
        country: 'Country',
        save_profile: 'Save profile',
        security_kicker: 'SECURITY',
        password_title: 'Password',
        current_password: 'Current password',
        new_password: 'New password',
        update_password: 'Update',
        owner: 'OWNER',
        active: 'ACTIVE',
        monthly_plan: 'MONTHLY',
        yearly_plan: 'YEARLY',
        lifetime: 'LIFETIME',
        trial: 'TRIAL',
        past_due: 'PAYMENT PAST DUE',
        canceled: 'CANCELED',
        email_to_confirm: 'EMAIL TO CONFIRM',
        payment_required: 'PAYMENT REQUIRED',
        inactive: 'INACTIVE',
        owner_account: 'Owner account',
        email_unconfirmed: 'Email not confirmed',
        active_stripe: 'Active via Stripe',
        stripe_linked: 'Stripe linked',
        waiting_payment: 'Waiting for payment',
        stripe_unlinked: 'Not linked to Stripe',
        status_active_title: 'Terminal access active',
        status_payment_title: 'Stripe payment required',
        status_confirm_title: 'Email to confirm',
        status_active_copy: 'Your account can open the full terminal. Billing remains manageable through Stripe.',
        status_payment_copy: 'Your email is confirmed. Choose a plan to start your trial and link Stripe to the account.',
        status_confirm_copy: 'Confirm your email before choosing a Stripe plan.',
        billing_active_copy: 'Your subscription is linked to Stripe. You can manage invoices, payment methods, plan changes and cancellations from the Stripe portal.',
        billing_ready_copy: 'Your email is confirmed. Choose a plan to start your trial and automatically link Stripe to your XAUTERMINAL account.',
        billing_confirm_copy: 'Confirm your email before choosing a plan. Stripe will then manage payment methods, invoices and cancellations.',
        stripe_portal_ready: 'Open Stripe portal',
        stripe_portal_missing: 'A Stripe payment must be linked before opening the portal',
        choose_plan_ready: 'Choose this plan via Stripe',
        choose_plan_missing: 'Confirm your email before choosing a plan',
        saving: 'Saving...',
        profile_saved: 'Profile saved.',
        profile_error: 'Unable to save profile.',
        updating: 'Updating...',
        password_saved: 'Password updated.',
        password_error: 'Password not changed.',
        redirect_stripe: 'Redirecting to Stripe...',
        payment_unavailable: 'Payment unavailable.',
        opening_portal: 'Opening Stripe portal...',
        portal_unavailable: 'Stripe portal unavailable.',
        sending_code: 'Sending code...',
        code_sent: 'Confirmation code sent again by email.',
        code_error: 'Code not sent.',
        payment_canceled: 'Payment canceled. You can choose a plan whenever you want.',
        validating_payment: 'Validating Stripe payment...',
        payment_valid: 'Payment valid. Your access is active.',
        payment_pending: 'Payment received, sync pending.',
    },
};

function t(key) {
    return ACCOUNT_COPY[accountLang]?.[key] || ACCOUNT_COPY.fr[key] || key;
}

function applyAccountLanguage() {
    document.documentElement.lang = accountLang;
    document.querySelectorAll('[data-i18n]').forEach((el) => {
        el.textContent = t(el.dataset.i18n);
    });
    const title = document.querySelector('title');
    if (title?.dataset.i18n) title.textContent = t(title.dataset.i18n);
    const toggle = document.querySelector('[data-account-lang-toggle]');
    if (toggle) toggle.textContent = accountLang === 'fr' ? 'EN' : 'FR';
    if (state.account) renderAccount(state.account);
}

function setText(id, value = '-') {
    const el = document.getElementById(id);
    if (el) el.textContent = value || '-';
}

function setValue(id, value = '') {
    const el = document.getElementById(id);
    if (el) el.value = value || '';
}

function setMessage(id, message = '', tone = '') {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = message;
    el.className = `account-message${tone ? ` ${tone}` : ''}`;
}

async function readJson(response) {
    const payload = await response.json();
    if (!response.ok) {
        throw new Error(payload.detail || 'Action impossible');
    }
    return payload;
}

function formatDate(value) {
    if (!value) return '-';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '-';
    return date.toLocaleDateString(accountLang === 'fr' ? 'fr-FR' : 'en-US', {
        day: '2-digit',
        month: 'long',
        year: 'numeric',
    });
}

function shortId(value) {
    if (!value) return '-';
    if (value.length <= 18) return value;
    return `${value.slice(0, 10)}...${value.slice(-6)}`;
}

function planLabel(account) {
    const plan = account.plan || account.role || '-';
    const labels = {
        owner: 'OWNER',
        active: t('active'),
        monthly: t('monthly_plan'),
        yearly: t('yearly_plan'),
        lifetime: t('lifetime'),
        trial: t('trial'),
    };
    return labels[plan] || String(plan).toUpperCase();
}

function accessLabel(account) {
    if (account.role === 'owner') return 'OWNER';
    if (account.status === 'past_due') return t('past_due');
    if (account.status === 'canceled') return t('canceled');
    if (account.has_access) return t('active');
    if (!account.email_confirmed) return t('email_to_confirm');
    if (account.status === 'confirmed') return t('payment_required');
    return String(account.status || t('inactive')).toUpperCase();
}

function billingStateLabel(account) {
    if (account.role === 'owner') return t('owner_account');
    if (!account.email_confirmed) return t('email_unconfirmed');
    if (account.stripe_customer_id && account.has_access) return t('active_stripe');
    if (account.stripe_customer_id) return t('stripe_linked');
    if (account.status === 'confirmed') return t('waiting_payment');
    return t('stripe_unlinked');
}

function billingCopy(account) {
    if (account.stripe_customer_id && account.has_access) {
        return t('billing_active_copy');
    }
    if (account.email_confirmed) {
        return t('billing_ready_copy');
    }
    return t('billing_confirm_copy');
}

function fillProfile(account) {
    const profile = account.profile || {};
    setValue('profile-first-name', profile.first_name);
    setValue('profile-last-name', profile.last_name);
    setValue('profile-address-line', profile.address_line);
    setValue('profile-postal-code', profile.postal_code);
    setValue('profile-city', profile.city);
    setValue('profile-country', profile.country);
}

function updateActionStates(account) {
    const portalButton = document.getElementById('account-portal');
    const resendButton = document.getElementById('account-resend-confirmation');
    const adminPanel = document.getElementById('account-admin-panel');
    const planButtons = document.querySelectorAll('[data-account-plan]');

    if (portalButton) {
        portalButton.disabled = !account.stripe_customer_id;
        portalButton.title = account.stripe_customer_id
            ? t('stripe_portal_ready')
            : t('stripe_portal_missing');
    }

    if (resendButton) {
        resendButton.hidden = !!account.email_confirmed;
    }

    if (adminPanel) {
        adminPanel.classList.toggle('hidden', account.role !== 'owner');
    }

    planButtons.forEach((button) => {
        button.disabled = !account.email_confirmed;
        button.title = account.email_confirmed
            ? t('choose_plan_ready')
            : t('choose_plan_missing');
    });
}

function renderAccount(account) {
    state.account = account;

    document.getElementById('account-login-state')?.classList.add('hidden');
    document.getElementById('account-dashboard')?.classList.remove('hidden');

    const hasAccess = !!account.has_access;
    const emailConfirmed = !!account.email_confirmed;
    const statusTitle = hasAccess
        ? t('status_active_title')
        : emailConfirmed
        ? t('status_payment_title')
        : t('status_confirm_title');
    const statusCopy = hasAccess
        ? t('status_active_copy')
        : emailConfirmed
        ? t('status_payment_copy')
        : t('status_confirm_copy');

    setText('account-status-title', statusTitle);
    setText('account-status-copy', statusCopy);
    setText('account-billing-copy', billingCopy(account));
    setText('account-status-badge', accessLabel(account));
    setText('account-email', account.email);
    setText('account-plan', planLabel(account));
    setText('account-access', accessLabel(account));
    setText('account-period-end', formatDate(account.stripe_current_period_end || account.trial_ends_at));
    setText('account-billing-state', billingStateLabel(account));
    setText('account-stripe-customer', shortId(account.stripe_customer_id));
    setText('account-stripe-subscription', shortId(account.stripe_subscription_id));
    setText('account-stripe-price', shortId(account.stripe_price_id));

    fillProfile(account);
    updateActionStates(account);
}

async function fetchAccount() {
    const response = await fetch('/api/account/me', { cache: 'no-store' });
    const payload = await readJson(response);
    if (!payload.authenticated || !payload.account) {
        document.getElementById('account-login-state')?.classList.remove('hidden');
        document.getElementById('account-dashboard')?.classList.add('hidden');
        return;
    }
    renderAccount(payload.account);
}

async function saveProfile(event) {
    event.preventDefault();
    try {
        setMessage('account-message', t('saving'));
        const response = await fetch('/api/account/profile', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                first_name: document.getElementById('profile-first-name')?.value || '',
                last_name: document.getElementById('profile-last-name')?.value || '',
                address_line: document.getElementById('profile-address-line')?.value || '',
                postal_code: document.getElementById('profile-postal-code')?.value || '',
                city: document.getElementById('profile-city')?.value || '',
                country: document.getElementById('profile-country')?.value || '',
            }),
        });
        const payload = await readJson(response);
        renderAccount(payload.account);
        setMessage('account-message', t('profile_saved'), 'ok');
    } catch (error) {
        setMessage('account-message', error.message || t('profile_error'), 'err');
    }
}

async function savePassword(event) {
    event.preventDefault();
    try {
        const currentPassword = document.getElementById('password-current')?.value || '';
        const newPassword = document.getElementById('password-new')?.value || '';
        setMessage('account-password-message', t('updating'));
        const response = await fetch('/api/account/password', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword,
            }),
        });
        await readJson(response);
        document.getElementById('account-password-form')?.reset();
        setMessage('account-password-message', t('password_saved'), 'ok');
    } catch (error) {
        setMessage('account-password-message', error.message || t('password_error'), 'err');
    }
}

async function startCheckout(plan) {
    try {
        setMessage('account-message', t('redirect_stripe'));
        const response = await fetch('/api/billing/checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ plan, return_path: '/account' }),
        });
        const payload = await readJson(response);
        window.location.href = payload.url;
    } catch (error) {
        setMessage('account-message', error.message || t('payment_unavailable'), 'err');
    }
}

async function openPortal() {
    try {
        setMessage('account-message', t('opening_portal'));
        const response = await fetch('/api/billing/portal', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ return_path: '/account' }),
        });
        const payload = await readJson(response);
        window.location.href = payload.url;
    } catch (error) {
        setMessage('account-message', error.message || t('portal_unavailable'), 'err');
    }
}

async function resendConfirmation() {
    if (!state.account?.email) return;
    try {
        setMessage('account-message', t('sending_code'));
        const response = await fetch('/api/account/resend-confirmation', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email: state.account.email }),
        });
        await readJson(response);
        setMessage('account-message', t('code_sent'), 'ok');
    } catch (error) {
        setMessage('account-message', error.message || t('code_error'), 'err');
    }
}

async function syncBillingReturn() {
    const params = new URLSearchParams(window.location.search);
    const status = params.get('billing');
    const sessionId = params.get('session_id');
    if (status === 'canceled') {
        setMessage('account-message', t('payment_canceled'), 'err');
        window.history.replaceState({}, '', window.location.pathname);
        return;
    }
    if (status !== 'success' || !sessionId) return;

    try {
        setMessage('account-message', t('validating_payment'));
        const response = await fetch('/api/billing/sync-checkout', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId }),
        });
        await readJson(response);
        setMessage('account-message', t('payment_valid'), 'ok');
    } catch (error) {
        setMessage('account-message', error.message || t('payment_pending'), 'err');
    } finally {
        window.history.replaceState({}, '', window.location.pathname);
    }
}

async function logout() {
    await fetch('/api/account/logout', { method: 'POST' });
    window.location.href = '/';
}

function bindAccountPage() {
    document.getElementById('account-profile-form')?.addEventListener('submit', saveProfile);
    document.getElementById('account-password-form')?.addEventListener('submit', savePassword);
    document.getElementById('account-portal')?.addEventListener('click', openPortal);
    document.getElementById('account-resend-confirmation')?.addEventListener('click', resendConfirmation);
    document.getElementById('account-logout')?.addEventListener('click', logout);
    document.querySelector('[data-account-lang-toggle]')?.addEventListener('click', () => {
        accountLang = accountLang === 'fr' ? 'en' : 'fr';
        localStorage.setItem('xt_lang', accountLang);
        applyAccountLanguage();
    });
    document.querySelectorAll('[data-account-plan]').forEach((button) => {
        button.addEventListener('click', () => startCheckout(button.dataset.accountPlan));
    });
}

document.addEventListener('DOMContentLoaded', () => {
    bindAccountPage();
    applyAccountLanguage();
    (async () => {
        await syncBillingReturn();
        await fetchAccount();
    })().catch(() => {
        document.getElementById('account-login-state')?.classList.remove('hidden');
        document.getElementById('account-dashboard')?.classList.add('hidden');
    });
});
