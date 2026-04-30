export function renderMarketProfileSelect(profiles, currentMarketProfile) {
    const select = document.getElementById('market-profile');
    if (!select) return;

    select.innerHTML = Object.values(profiles).map((profile) => `
        <option value="${profile.id}" ${profile.id === currentMarketProfile ? 'selected' : ''}>${profile.label}</option>
    `).join('');
}

export function syncCommandSymbol(symbol) {
    const cmdInput = document.getElementById('cmd');
    if (cmdInput) cmdInput.value = symbol;
}

export function bindMarketProfileControls({ renderSelect, onChange }) {
    const select = document.getElementById('market-profile');
    if (!select) return;

    renderSelect();
    select.addEventListener('change', () => {
        onChange(select.value);
    });
}

export function setCenterTab(tab) {
    document.querySelectorAll('[data-center-tab]').forEach((button) => {
        button.classList.toggle('active', button.dataset.centerTab === tab);
    });

    document.querySelectorAll('[data-panel]').forEach((panel) => {
        panel.classList.toggle('active', panel.dataset.panel === tab);
    });
}

export function bindCenterTabs({ getCurrentTab, onChange }) {
    const tabs = document.querySelectorAll('[data-center-tab]');
    if (!tabs.length) return;

    tabs.forEach((button) => {
        button.addEventListener('click', () => {
            const { centerTab } = button.dataset;
            if (!centerTab) return;
            onChange(centerTab);
        });
    });

    setCenterTab(getCurrentTab());
}

export function initChart(symbol) {
    const wrap = document.getElementById('tv_main_wrap');
    if (!wrap) return;

    wrap.innerHTML = '<div id="tv_main" style="height:100%;"></div>';

    const symbolLabel = document.getElementById('chart-symbol');
    if (symbolLabel) {
        symbolLabel.textContent = symbol;
    }

    new TradingView.widget({
        autosize: true,
        symbol,
        interval: '1',
        theme: 'dark',
        style: '1',
        locale: 'fr',
        container_id: 'tv_main',
        hide_side_toolbar: false,
        allow_symbol_change: true,
        details: true,
        studies: ['Volume@tv-basicstudies'],
    });
}

export function changeChart(symbol) {
    initChart(symbol);

    document.querySelectorAll('.qcard').forEach((card) => {
        card.classList.toggle('active', card.dataset.symbol === symbol);
    });
}

export function bindCommandInput({ getCurrentSymbol, onChange }) {
    const input = document.getElementById('cmd');
    if (!input) return;

    input.value = getCurrentSymbol();
    input.addEventListener('keydown', (event) => {
        if (event.key !== 'Enter') return;

        const value = input.value.trim().toUpperCase();
        if (!value) return;
        onChange(value);
    });
}
