function highlightActiveNav() {
    const path = window.location.pathname || '';
    document.querySelectorAll('.sidebar-nav a[data-nav]').forEach(function (a) {
        const t = a.getAttribute('data-nav');
        if (!t) {
            return;
        }
        if (path === t || path.startsWith(t + '/')) {
            a.classList.add('active');
        }
    });
}

function parseUtcDateTime(dateStr) {
    if (dateStr == null || dateStr === '') {
        return null;
    }
    const s = String(dateStr).trim();
    if (!s || s === '—') {
        return null;
    }
    if (/^\d{4}-\d{2}-\d{2}$/.test(s)) {
        return new Date(s + 'T00:00:00.000Z');
    }
    if (/^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}/.test(s)) {
        const normalized = s.indexOf('T') >= 0 ? s : s.replace(' ', 'T');
        if (/Z$/i.test(normalized) || /[+-]\d{2}:\d{2}$/.test(normalized)) {
            const d2 = new Date(normalized);
            return isNaN(d2.getTime()) ? null : d2;
        }
        const d3 = new Date(normalized + 'Z');
        return isNaN(d3.getTime()) ? null : d3;
    }
    const d = new Date(s);
    return isNaN(d.getTime()) ? null : d;
}

function formatDate(dateStr) {
    const d = parseUtcDateTime(dateStr);
    if (!d) {
        return dateStr ? String(dateStr) : '—';
    }
    try {
        return d.toLocaleString('ar-SA', { dateStyle: 'medium', timeStyle: 'short' });
    } catch (e) {
        return String(dateStr);
    }
}

function applyLocalDates(root) {
    var scope = root || document;
    scope.querySelectorAll('[data-utc-datetime]').forEach(function (el) {
        var v = el.getAttribute('data-utc-datetime');
        if (v == null || v === '') {
            return;
        }
        el.textContent = formatDate(v);
    });
}

function formatDuration(seconds) {
    const s = Math.max(0, Math.floor(Number(seconds) || 0));
    const m = Math.floor(s / 60);
    const r = s % 60;
    return m + ' دقيقة ' + r + ' ثانية';
}

function showToast(msg, type) {
    const host = document.getElementById('toastHost');
    if (!host) {
        return;
    }
    const el = document.createElement('div');
    el.className = 'toast ' + (type || 'warning');
    el.textContent = msg;
    host.appendChild(el);
    setTimeout(function () {
        el.remove();
    }, 4000);
}

async function refreshHeaderStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        if (!data.ok) {
            return;
        }
        const n = data.active_alerts != null ? data.active_alerts : 0;
        const top = document.getElementById('topbarAlertCount');
        if (top) {
            top.textContent = String(n);
        }
        const badge = document.getElementById('sidebarAlertBadge');
        if (badge) {
            badge.textContent = String(n);
            badge.classList.toggle('is-hidden', n === 0);
        }
    } catch (e) {}
}

function initMobileNav() {
    var toggle = document.getElementById('navToggle');
    var sidebar = document.getElementById('sidebar');
    var backdrop = document.getElementById('sidebarBackdrop');
    if (!toggle || !sidebar || !backdrop) {
        return;
    }
    var icon = toggle.querySelector('i');
    function isMobile() {
        return window.matchMedia('(max-width: 768px)').matches;
    }
    function openMenu() {
        sidebar.classList.add('is-open');
        backdrop.classList.add('is-visible');
        document.body.classList.add('sidebar-open');
        toggle.setAttribute('aria-expanded', 'true');
        toggle.setAttribute('aria-label', 'إغلاق القائمة');
        if (icon) {
            icon.className = 'fa-solid fa-xmark';
        }
    }
    function closeMenu() {
        sidebar.classList.remove('is-open');
        backdrop.classList.remove('is-visible');
        document.body.classList.remove('sidebar-open');
        toggle.setAttribute('aria-expanded', 'false');
        toggle.setAttribute('aria-label', 'فتح القائمة');
        if (icon) {
            icon.className = 'fa-solid fa-bars';
        }
    }
    toggle.addEventListener('click', function () {
        if (sidebar.classList.contains('is-open')) {
            closeMenu();
        } else {
            openMenu();
        }
    });
    backdrop.addEventListener('click', closeMenu);
    document.querySelectorAll('.sidebar-nav a').forEach(function (a) {
        a.addEventListener('click', function () {
            if (isMobile()) {
                closeMenu();
            }
        });
    });
    window.addEventListener('resize', function () {
        if (!isMobile()) {
            closeMenu();
        }
    });
}

document.addEventListener('DOMContentLoaded', function () {
    highlightActiveNav();
    initMobileNav();
    applyLocalDates();
    refreshHeaderStats();
    setInterval(refreshHeaderStats, 60000);
});

window.formatDate = formatDate;
window.formatDuration = formatDuration;
window.showToast = showToast;
window.refreshHeaderStats = refreshHeaderStats;
window.applyLocalDates = applyLocalDates;
