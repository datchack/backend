const CATEGORY_ALL = 'all';

function normalize(value) {
    return String(value || '').toLowerCase().replace(/[^a-z0-9]/g, '');
}

function profileMatches(profile, query) {
    if (!query) return true;
    const haystack = normalize(`${profile.label} ${profile.symbol} ${profile.description || ''}`);
    return haystack.includes(normalize(query));
}

function profileCategory(profile) {
    return profile.category || 'forex_major';
}

function formatSymbolLabel(symbol) {
    const clean = String(symbol || '').split(':').pop().toUpperCase().replace(/[^A-Z0-9]/g, '');
    if (clean.length === 6 && /^[A-Z]{6}$/.test(clean)) {
        return `${clean.slice(0, 3)}/${clean.slice(3)}`;
    }
    return clean || symbol;
}

function buildCustomSymbol(query) {
    const raw = String(query || '').trim().toUpperCase();
    const clean = raw.replace(/[^A-Z0-9]/g, '');
    if (!clean || clean.length < 2) return null;
    if (raw.includes(':')) return raw;
    if (['XAUUSD', 'XAGUSD'].includes(clean)) return `OANDA:${clean}`;
    if (/^[A-Z]{6}$/.test(clean)) return `FX:${clean}`;
    if (['BTCUSD', 'ETHUSD', 'SOLUSD', 'XRPUSD'].includes(clean)) return `BITSTAMP:${clean}`;
    return clean;
}

export function renderCompactProfileSelect(profiles, currentMarketProfile) {
    const select = document.getElementById('market-profile');
    if (!select) return;

    const featured = Object.values(profiles).filter((profile) => profile.featured);
    const active = profiles[currentMarketProfile];
    const items = active && !featured.some((profile) => profile.id === active.id)
        ? [active, ...featured]
        : featured;

    select.innerHTML = items.map((profile) => `
        <option value="${profile.id}" ${profile.id === currentMarketProfile ? 'selected' : ''}>${profile.label}</option>
    `).join('');
}

export function bindMarketSelector({
    profiles,
    categories,
    getCurrentProfile,
    getFavorites,
    setFavorites,
    onSelect,
    onCustomSymbol,
}) {
    const openButton = document.getElementById('market-selector-open');
    const overlay = document.getElementById('market-selector');
    const closeButton = document.getElementById('market-selector-close');
    const searchInput = document.getElementById('market-selector-search');
    const categoryRoot = document.getElementById('market-selector-categories');
    const gridRoot = document.getElementById('market-selector-grid');
    const countEl = document.getElementById('market-selector-count');
    if (!openButton || !overlay || !closeButton || !searchInput || !categoryRoot || !gridRoot) return;

    let activeCategory = CATEGORY_ALL;
    const allCategories = [{ id: CATEGORY_ALL, label: 'Tous' }, ...categories];

    function close() {
        overlay.classList.add('hidden');
        openButton.focus();
    }

    function open() {
        overlay.classList.remove('hidden');
        searchInput.focus();
        render();
    }

    function renderCategories() {
        categoryRoot.innerHTML = allCategories.map((category) => `
            <button type="button" class="market-filter ${category.id === activeCategory ? 'active' : ''}" data-market-category="${category.id}">
                ${category.label}
            </button>
        `).join('');

        categoryRoot.querySelectorAll('[data-market-category]').forEach((button) => {
            button.addEventListener('click', () => {
                activeCategory = button.dataset.marketCategory || CATEGORY_ALL;
                render();
            });
        });
    }

    function render() {
        const query = searchInput.value.trim();
        const currentProfile = getCurrentProfile();
        const favorites = new Set(getFavorites());
        const items = Object.values(profiles).filter((profile) => {
            const matchesCategory = activeCategory === CATEGORY_ALL
                || (activeCategory === 'favorites' ? favorites.has(profile.id) : profileCategory(profile) === activeCategory);
            return matchesCategory && profileMatches(profile, query);
        });
        const customSymbol = buildCustomSymbol(query);
        const hasExactProfile = customSymbol && Object.values(profiles).some((profile) => normalize(profile.symbol) === normalize(customSymbol));
        const showCustom = !!customSymbol && activeCategory !== 'favorites' && !hasExactProfile;
        const resultCount = items.length + (showCustom ? 1 : 0);

        if (countEl) {
            countEl.textContent = `${resultCount} marché${resultCount > 1 ? 's' : ''}`;
        }

        const profileCards = items.map((profile) => {
                const isActive = profile.id === currentProfile;
                const isFavorite = favorites.has(profile.id);
                return `
                    <article class="market-select-card ${isActive ? 'active' : ''}">
                        <button type="button" class="market-favorite ${isFavorite ? 'active' : ''}" data-market-favorite="${profile.id}" aria-label="Favori ${profile.label}">${isFavorite ? '★' : '☆'}</button>
                        <button type="button" class="market-select-main" data-market-select="${profile.id}">
                            <span>${profile.label}</span>
                            <strong>${profile.symbol}</strong>
                            <em>${profile.description || 'Market profile'}</em>
                        </button>
                    </article>`;
            }).join('');
        const customCard = showCustom
            ? `
                <article class="market-select-card custom">
                    <button type="button" class="market-select-main" data-market-custom-symbol="${customSymbol}">
                        <span>${formatSymbolLabel(customSymbol)}</span>
                        <strong>${customSymbol}</strong>
                        <em>Charger ce symbole TradingView et générer un Bias dynamique quand les données sont disponibles.</em>
                    </button>
                </article>`
            : '';
        gridRoot.innerHTML = profileCards || customCard
            ? `${profileCards}${customCard}`
            : '<div class="market-selector-empty">Aucun marché trouvé. Essaie un symbole TradingView comme FX:GBPJPY ou NASDAQ:AAPL.</div>';

        gridRoot.querySelectorAll('[data-market-select]').forEach((button) => {
            button.addEventListener('click', () => {
                const profileId = button.dataset.marketSelect;
                if (!profileId) return;
                onSelect(profileId);
                close();
            });
        });

        gridRoot.querySelectorAll('[data-market-custom-symbol]').forEach((button) => {
            button.addEventListener('click', () => {
                const symbol = button.dataset.marketCustomSymbol;
                if (!symbol) return;
                onCustomSymbol?.(symbol);
                close();
            });
        });

        gridRoot.querySelectorAll('[data-market-favorite]').forEach((button) => {
            button.addEventListener('click', (event) => {
                event.stopPropagation();
                const profileId = button.dataset.marketFavorite;
                if (!profileId) return;
                const nextFavorites = new Set(getFavorites());
                if (nextFavorites.has(profileId)) {
                    nextFavorites.delete(profileId);
                } else {
                    nextFavorites.add(profileId);
                }
                setFavorites([...nextFavorites]);
                render();
            });
        });
    }

    renderCategories();
    render();
    openButton.addEventListener('click', open);
    closeButton.addEventListener('click', close);
    searchInput.addEventListener('input', render);
    overlay.addEventListener('click', (event) => {
        if (event.target === overlay) close();
    });
    window.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && !overlay.classList.contains('hidden')) close();
    });
}
