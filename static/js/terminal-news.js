import { sourceClass } from './terminal-formatters.js';

function renderNewsSummaries(items) {
    const priorityEl = document.getElementById('news-priority-summary');
    const officialEl = document.getElementById('official-summary');
    if (!priorityEl || !officialEl) return;

    const high = items.filter((item) => item.priority === 'high').length;
    const official = items.filter((item) => (item.tags || []).includes('OFFICIAL')).length;
    const moving = items.filter((item) => item.market_moving).length;

    const matched = items.filter((item) => Number(item.profile_score || 0) > 0).length;
    priorityEl.textContent = `MOVING ${moving} / MATCH ${matched}`;
    officialEl.textContent = `HIGH ${high} / OFFICIAL ${official}`;
}

function renderNewsItem(itemData, { isFresh }) {
    const item = document.createElement('div');
    item.className = `n-item ${itemData.priority || 'low'}${itemData.crit ? ' critical' : ''}${itemData.market_moving ? ' moving' : ''}${isFresh ? ' fresh' : ''}`;

    const meta = document.createElement('div');
    meta.className = 'n-meta';

    const time = document.createElement('span');
    time.textContent = itemData.time;

    const source = document.createElement('span');
    source.className = `tag ${sourceClass(itemData.s)}`;
    source.textContent = itemData.s;

    const priority = document.createElement('span');
    priority.className = `tag priority ${itemData.priority || 'low'}`;
    priority.textContent = (itemData.priority || 'low').toUpperCase();

    meta.appendChild(time);
    meta.appendChild(source);
    meta.appendChild(priority);

    if (itemData.market_moving) {
        const moving = document.createElement('span');
        moving.className = 'tag moving';
        moving.textContent = 'MOVING';
        meta.appendChild(moving);
    }

    (itemData.tags || []).slice(0, 3).forEach((tagName) => {
        const tag = document.createElement('span');
        tag.className = `tag topic ${tagName.toLowerCase()}`;
        tag.textContent = tagName;
        meta.appendChild(tag);
    });

    const link = document.createElement('a');
    link.href = itemData.l;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.textContent = itemData.t;

    item.appendChild(meta);
    item.appendChild(link);

    if (Number(itemData.duplicate_count || 1) > 1 || (itemData.related_sources || []).length > 1) {
        const cluster = document.createElement('div');
        cluster.className = 'n-cluster';
        const sources = (itemData.related_sources || []).join(' + ');
        cluster.textContent = `${itemData.duplicate_count || 1} sources: ${sources}`;
        item.appendChild(cluster);
    }

    return item;
}

export function renderNewsFeed(data, state) {
    const items = data.items || [];
    const container = document.getElementById('news-content');

    if (!container) {
        return { state, freshAlertCount: 0, suppressFresh: state.suppressNextFresh };
    }

    container.innerHTML = '';

    let freshAlertCount = 0;
    const suppressFresh = state.suppressNextFresh;
    const alertedNewsIds = new Set(state.alertedNewsIds);

    renderNewsSummaries(items);

    items.forEach((itemData) => {
        const newsId = itemData.id || `${itemData.s}:${itemData.ts}:${itemData.t}`;
        const isFresh = state.hasLoaded && !suppressFresh && itemData.ts > state.lastSeenTs && !alertedNewsIds.has(newsId);
        const shouldAlert = isFresh && (itemData.market_moving || itemData.priority === 'high' || itemData.crit);
        if (shouldAlert) {
            freshAlertCount += 1;
            alertedNewsIds.add(newsId);
        }

        container.appendChild(renderNewsItem(itemData, { isFresh }));
    });

    const latestNewsTs = items.reduce((latest, item) => Math.max(latest, Number(item.ts) || 0), state.lastSeenTs);
    const nextLastSeenTs = latestNewsTs > state.lastSeenTs ? latestNewsTs : state.lastSeenTs;

    const statusNews = document.getElementById('status-news');
    if (statusNews) {
        const highCount = items.filter((item) => item.priority === 'high').length;
        const matchedCount = items.filter((item) => Number(item.profile_score || 0) > 0).length;
        statusNews.textContent = `News: ${items.length} items - match ${matchedCount} - high ${highCount} - ${data.window_hours || 72}h${data.cached ? ` - cache ${data.age}s` : ''}`;
    }

    return {
        state: {
            lastSeenTs: nextLastSeenTs,
            hasLoaded: true,
            suppressNextFresh: false,
            alertedNewsIds,
        },
        freshAlertCount,
        suppressFresh,
    };
}

export function renderNewsError() {
    const statusNews = document.getElementById('status-news');
    if (statusNews) {
        statusNews.textContent = 'News: erreur de chargement';
    }
}
