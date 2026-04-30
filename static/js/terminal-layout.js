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
