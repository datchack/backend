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

        if (countEl) {
            countEl.textContent = `${items.length} marché${items.length > 1 ? 's' : ''}`;
        }

        gridRoot.innerHTML = items.length
            ? items.map((profile) => {
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
            }).join('')
            : '<div class="market-selector-empty">Aucun marché trouvé.</div>';

        gridRoot.querySelectorAll('[data-market-select]').forEach((button) => {
            button.addEventListener('click', () => {
                const profileId = button.dataset.marketSelect;
                if (!profileId) return;
                onSelect(profileId);
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
