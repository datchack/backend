import { DEFAULT_LAYOUT } from './terminal-config.js';

export function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
}

export function loadLayoutPrefs(source = null) {
    const raw = source || {};
    return {
        leftWidth: clamp(Number(raw.leftWidth) || DEFAULT_LAYOUT.leftWidth, 260, 520),
        rightWidth: clamp(Number(raw.rightWidth) || DEFAULT_LAYOUT.rightWidth, 260, 520),
        insightWidth: clamp(Number(raw.insightWidth) || DEFAULT_LAYOUT.insightWidth, 260, 520),
        collapsed: {
            left: !!raw.collapsed?.left,
            right: !!raw.collapsed?.right,
            chart: !!raw.collapsed?.chart,
            insight: !!raw.collapsed?.insight,
        },
    };
}

export function defaultLayoutState() {
    return {
        leftWidth: DEFAULT_LAYOUT.leftWidth,
        rightWidth: DEFAULT_LAYOUT.rightWidth,
        insightWidth: DEFAULT_LAYOUT.insightWidth,
        collapsed: { ...DEFAULT_LAYOUT.collapsed },
    };
}

function updateToggleButtons(panel, collapsed) {
    document.querySelectorAll(`.panel-btn[data-toggle-panel="${panel}"]`).forEach((button) => {
        button.textContent = collapsed ? '+' : '-';
        button.title = collapsed ? 'Ouvrir le panel' : 'Reduire le panel';
    });
}

export function applyLayoutState(layoutState) {
    const root = document.documentElement;
    const mainLayout = document.querySelector('.main-layout');
    const centerShell = document.querySelector('.center-shell');

    root.style.setProperty('--left-width', `${layoutState.leftWidth}px`);
    root.style.setProperty('--right-width', `${layoutState.rightWidth}px`);
    root.style.setProperty('--insight-width', `${layoutState.insightWidth}px`);

    if (mainLayout) {
        mainLayout.dataset.leftCollapsed = String(layoutState.collapsed.left);
        mainLayout.dataset.rightCollapsed = String(layoutState.collapsed.right);
    }

    if (centerShell) {
        centerShell.dataset.chartCollapsed = String(layoutState.collapsed.chart);
        centerShell.dataset.insightCollapsed = String(layoutState.collapsed.insight);
    }

    ['left', 'right', 'chart', 'insight'].forEach((panel) => {
        const el = document.querySelector(`[data-layout-panel="${panel}"]`);
        if (el) {
            el.dataset.collapsed = String(layoutState.collapsed[panel]);
        }
        updateToggleButtons(panel, layoutState.collapsed[panel]);
    });
}

export function applyWidgetVisibility(widgetVisibility) {
    document.body.dataset.showTicker = String(widgetVisibility.ticker !== false);
    document.body.dataset.showQuotes = String(widgetVisibility.quotes !== false);
    document.body.dataset.showCalendar = String(widgetVisibility.calendar !== false);
    document.body.dataset.showChart = String(widgetVisibility.chart !== false);
    document.body.dataset.showBias = String(widgetVisibility.bias !== false);
    document.body.dataset.showNews = String(widgetVisibility.news !== false);
}

function togglePanel(panel, layoutState, persistLayout) {
    if (panel === 'chart' && !layoutState.collapsed.chart && layoutState.collapsed.insight) {
        layoutState.collapsed.insight = false;
    }
    if (panel === 'insight' && !layoutState.collapsed.insight && layoutState.collapsed.chart) {
        layoutState.collapsed.chart = false;
    }

    layoutState.collapsed[panel] = !layoutState.collapsed[panel];
    applyLayoutState(layoutState);
    persistLayout();
}

export function bindLayoutControls({ getLayoutState, setLayoutState, persistLayout }) {
    document.querySelectorAll('[data-toggle-panel]').forEach((button) => {
        button.addEventListener('click', () => {
            const panel = button.dataset.togglePanel;
            if (!panel) return;
            togglePanel(panel, getLayoutState(), persistLayout);
        });
    });

    ['layout-reset', 'layout-reset-status'].forEach((id) => {
        const button = document.getElementById(id);
        if (!button) return;
        button.addEventListener('click', () => {
            const nextLayoutState = defaultLayoutState();
            setLayoutState(nextLayoutState);
            applyLayoutState(nextLayoutState);
            persistLayout();
        });
    });

    applyLayoutState(getLayoutState());
}

export function bindResizers({ getLayoutState, persistLayout }) {
    document.querySelectorAll('[data-resize]').forEach((handle) => {
        handle.addEventListener('pointerdown', (event) => {
            const mode = handle.dataset.resize;
            const mainLayout = document.querySelector('.main-layout');
            const centerShell = document.querySelector('.center-shell');
            const layoutState = getLayoutState();

            if (!mode || !mainLayout || !centerShell) return;
            if ((mode === 'left' || mode === 'right') && window.innerWidth < 1180) return;
            if (mode === 'insight' && (window.innerWidth < 1400 || layoutState.collapsed.chart || layoutState.collapsed.insight)) return;

            event.preventDefault();
            handle.classList.add('dragging');

            const onMove = (moveEvent) => {
                if (mode === 'left') {
                    const rect = mainLayout.getBoundingClientRect();
                    layoutState.leftWidth = clamp(moveEvent.clientX - rect.left, 260, 520);
                } else if (mode === 'right') {
                    const rect = mainLayout.getBoundingClientRect();
                    layoutState.rightWidth = clamp(rect.right - moveEvent.clientX, 260, 520);
                } else if (mode === 'insight') {
                    const rect = centerShell.getBoundingClientRect();
                    layoutState.insightWidth = clamp(rect.right - moveEvent.clientX, 260, Math.min(520, rect.width - 260));
                }

                applyLayoutState(layoutState);
            };

            const onUp = () => {
                handle.classList.remove('dragging');
                window.removeEventListener('pointermove', onMove);
                window.removeEventListener('pointerup', onUp);
                persistLayout();
            };

            window.addEventListener('pointermove', onMove);
            window.addEventListener('pointerup', onUp);
        });
    });
}
