const CATEGORY_ALL = 'all';
const MAX_RECENT_ITEMS = 8;

function normalize(value) {
    return String(value || '').toLowerCase().replace(/[^a-z0-9]/g, '');
}

function normalizeSymbol(value) {
    return normalize(String(value || '').split(':').pop());
}

function profileMatches(profile, query) {
    if (!query) return true;
    const symbol = String(profile.symbol || '');
    const category = profileCategory(profile);
    const haystack = normalize([
        profile.label,
        symbol,
        symbol.split(':').pop(),
        profile.description,
        profile.aliases?.join(' '),
        profile.countries?.join(' '),
        category,
    ].join(' '));
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

function categoryLabelMap(categories) {
    return Object.fromEntries(categories.map((category) => [category.id, category.label]));
}

function compactSymbol(symbol) {
    return String(symbol || '').replace(/^[A-Z]+:/, '');
}

function normalizeRecentItem(item) {
    if (!item) return null;
    if (typeof item === 'string') {
        return { type: 'profile', id: item };
    }
    if (item.type === 'symbol' && item.symbol) {
        return { type: 'symbol', symbol: item.symbol, label: item.label || formatSymbolLabel(item.symbol) };
    }
    if (item.type === 'profile' && item.id) {
        return { type: 'profile', id: item.id };
    }
    if (item.id) {
        return { type: 'profile', id: item.id };
    }
    return null;
}

function getRecentItems(recents, profiles) {
    return (recents || [])
        .map(normalizeRecentItem)
        .filter(Boolean)
        .filter((item, index, list) => {
            const key = item.type === 'symbol' ? normalizeSymbol(item.symbol) : item.id;
            return list.findIndex((candidate) => (
                candidate.type === item.type
                && (candidate.type === 'symbol' ? normalizeSymbol(candidate.symbol) : candidate.id) === key
            )) === index;
        })
        .filter((item) => item.type === 'symbol' || profiles[item.id])
        .slice(0, MAX_RECENT_ITEMS);
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

export function renderWorkspacePresetSelect(presets, currentWorkspacePreset) {
    const select = document.getElementById('market-profile');
    if (!select) return;

    const items = Object.values(presets || {});
    const placeholder = currentWorkspacePreset ? '' : '<option value="" selected>WORKSPACE</option>';
    select.innerHTML = `${placeholder}${items.map((preset) => `
        <option value="${preset.id}" ${preset.id === currentWorkspacePreset ? 'selected' : ''}>${preset.label}</option>
    `).join('')}`;
}

export function bindMarketSelector({
    profiles,
    categories,
    getCurrentProfile,
    getFavorites,
    getRecents,
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
    const categoryLabels = categoryLabelMap(categories);

    function close() {
        overlay.classList.add('hidden');
        openButton.focus();
    }

    function open() {
        overlay.classList.remove('hidden');
        activeCategory = CATEGORY_ALL;
        searchInput.value = '';
        renderCategories();
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
                renderCategories();
                render();
            });
        });
    }

    function renderProfileCard(profile, currentProfile, favorites) {
        const isActive = profile.id === currentProfile;
        const isFavorite = favorites.has(profile.id);
        const category = categoryLabels[profileCategory(profile)] || profileCategory(profile);
        const countries = Array.isArray(profile.countries) && profile.countries.length ? profile.countries.join(' / ') : 'Global';
        const status = profile.featured ? 'Preset prioritaire' : 'Preset complet';

        return `
            <article class="market-select-card ${isActive ? 'active' : ''}">
                <button type="button" class="market-favorite ${isFavorite ? 'active' : ''}" data-market-favorite="${profile.id}" aria-label="Favori ${profile.label}">${isFavorite ? '★' : '☆'}</button>
                <button type="button" class="market-select-main" data-market-select="${profile.id}">
                    <span>${profile.label}</span>
                    <strong>${compactSymbol(profile.symbol)}</strong>
                    <em>${profile.description || 'Market profile'}</em>
                    <small class="market-card-meta">
                        <b>${category}</b>
                        <b>${countries}</b>
                        <b>${status}</b>
                    </small>
                    <i class="market-card-action">OUVRIR</i>
                </button>
            </article>`;
    }

    function renderCustomCard(customSymbol, extraClass = '') {
        return `
            <article class="market-select-card custom ${extraClass}">
                <button type="button" class="market-select-main" data-market-custom-symbol="${customSymbol}">
                    <span>${formatSymbolLabel(customSymbol)}</span>
                    <strong>${compactSymbol(customSymbol)}</strong>
                    <em>Charger ce symbole TradingView et générer un Bias dynamique quand les données sont disponibles.</em>
                    <small class="market-card-meta">
                        <b>Symbole libre</b>
                        <b>TradingView</b>
                        <b>Bias dynamique</b>
                    </small>
                    <i class="market-card-action">OUVRIR</i>
                </button>
            </article>`;
    }

    function renderSection(title, kicker, cards, options = {}) {
        if (!cards) return '';
        return `
            <section class="market-selector-section ${options.compact ? 'compact' : ''}">
                <div class="market-selector-section-head">
                    <span>${kicker}</span>
                    <h3>${title}</h3>
                </div>
                <div class="market-selector-cards">${cards}</div>
            </section>`;
    }

    function bindRenderedActions() {
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

    function render() {
        const query = searchInput.value.trim();
        const currentProfile = getCurrentProfile();
        const favorites = new Set(getFavorites());
        const recents = getRecentItems(getRecents?.() || [], profiles);
        const items = Object.values(profiles).filter((profile) => {
            const matchesCategory = activeCategory === CATEGORY_ALL
                || (activeCategory === 'favorites' ? favorites.has(profile.id) : profileCategory(profile) === activeCategory);
            return matchesCategory && profileMatches(profile, query);
        });
        const customSymbol = buildCustomSymbol(query);
        const hasExactProfile = customSymbol && Object.values(profiles).some((profile) => normalizeSymbol(profile.symbol) === normalizeSymbol(customSymbol));
        const showCustom = !!customSymbol && activeCategory !== 'favorites' && !hasExactProfile;
        const resultCount = items.length + (showCustom ? 1 : 0);

        if (countEl) {
            countEl.textContent = `${resultCount} marché${resultCount > 1 ? 's' : ''}`;
        }

        const profileCards = items.map((profile) => renderProfileCard(profile, currentProfile, favorites)).join('');
        const customCard = showCustom
            ? renderCustomCard(customSymbol)
            : '';

        if (!query && activeCategory === CATEGORY_ALL) {
            const favoriteCards = [...favorites]
                .map((id) => profiles[id])
                .filter(Boolean)
                .map((profile) => renderProfileCard(profile, currentProfile, favorites))
                .join('');
            const recentCards = recents.map((item) => {
                if (item.type === 'symbol') {
                    return renderCustomCard(item.symbol, 'recent');
                }
                return renderProfileCard(profiles[item.id], currentProfile, favorites);
            }).join('');
            const sections = [
                renderSection('Favoris', 'Accès rapide', favoriteCards, { compact: true }),
                renderSection('Récents', 'Dernières ouvertures', recentCards, { compact: true }),
                renderSection('Tous les marchés', 'Univers XAUTERMINAL', profileCards),
            ].join('');

            gridRoot.innerHTML = sections || '<div class="market-selector-empty">Aucun marché disponible.</div>';
            bindRenderedActions();
            return;
        }

        gridRoot.innerHTML = profileCards || customCard
            ? `<div class="market-selector-cards">${profileCards}${customCard}</div>`
            : '<div class="market-selector-empty">Aucun marché trouvé. Essaie un symbole TradingView comme FX:GBPJPY, XAG/USD ou NASDAQ:AAPL.</div>';

        bindRenderedActions();
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
