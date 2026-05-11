let alertsCache = [];

function buildQuery() {
    const sev = document.getElementById('fltSeverity');
    const st = document.getElementById('fltStatus');
    const params = new URLSearchParams();
    if (sev && sev.value) {
        params.set('severity', sev.value);
    }
    if (st && st.value) {
        params.set('status', st.value);
    }
    const q = params.toString();
    return q ? '?' + q : '';
}

async function deleteAlert(alertId) {
    if (!confirm('حذف هذا التنبيه نهائياً؟')) {
        return;
    }
    try {
        const res = await fetch('/api/alerts/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ alert_id: alertId }),
        });
        const data = await res.json();
        if (!data.ok) {
            if (window.showToast) {
                window.showToast(data.message || 'فشل الحذف', 'danger');
            }
            return;
        }
        if (window.showToast) {
            window.showToast('تم حذف التنبيه', 'success');
        }
        loadAlerts();
        if (typeof window.refreshHeaderStats === 'function') {
            window.refreshHeaderStats();
        }
    } catch (e) {
        if (window.showToast) {
            window.showToast('خطأ في الشبكة', 'danger');
        }
    }
}

async function loadAlerts() {
    try {
        const res = await fetch('/api/alerts' + buildQuery());
        const data = await res.json();
        const box = document.getElementById('alertsContainer');
        if (!box || !data.ok) {
            return;
        }
        alertsCache = data.items || [];
        box.innerHTML = '';
        if (!alertsCache.length) {
            box.innerHTML = '<div class="panel"><p style="font-weight:700;">لا توجد تنبيهات مطابقة.</p></div>';
            return;
        }
        alertsCache.forEach(function (a) {
            const card = document.createElement('div');
            card.className = 'alert-card';
            const sev = a.severity_level || '';
            let badgeClass = 'badge-info';
            if (sev === 'عالية') {
                badgeClass = 'badge-danger';
            } else if (sev === 'متوسطة') {
                badgeClass = 'badge-warning';
            } else if (sev === 'منخفضة') {
                badgeClass = 'badge-success';
            }
            const h = document.createElement('h3');
            h.textContent = a.threat_type || 'تنبيه';
            const meta = document.createElement('div');
            meta.className = 'alert-meta';
            meta.textContent =
                (window.formatDate ? window.formatDate(a.alert_timestamp) : a.alert_timestamp) +
                ' — الحالة: ' +
                (a.alert_status || '');
            const desc = document.createElement('p');
            desc.style.fontWeight = '700';
            desc.textContent = a.description || '';
            const reasons = document.createElement('div');
            reasons.className = 'alert-reasons';
            if (a.reasons_text) {
                reasons.textContent = 'الأسباب: ' + a.reasons_text;
            }
            const row = document.createElement('div');
            row.style.display = 'flex';
            row.style.flexWrap = 'wrap';
            row.style.gap = '10px';
            row.style.marginTop = '12px';
            row.style.alignItems = 'center';
            const span = document.createElement('span');
            span.className = 'badge ' + badgeClass;
            span.textContent = 'الخطورة: ' + sev;
            const sel = document.createElement('select');
            sel.style.maxWidth = '200px';
            ;['جديد', 'قيد المراجعة', 'مغلق'].forEach(function (v) {
                const opt = document.createElement('option');
                opt.value = v;
                opt.textContent = v;
                if (v === (a.alert_status || '')) {
                    opt.selected = true;
                }
                sel.appendChild(opt);
            });
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn btn-outline';
            btn.textContent = 'تحديث الحالة';
            btn.addEventListener('click', function () {
                updateAlertStatus(a.alert_id, sel.value);
            });
            const btnDel = document.createElement('button');
            btnDel.type = 'button';
            btnDel.className = 'btn-delete-record';
            btnDel.title = 'حذف التنبيه';
            btnDel.setAttribute('aria-label', 'حذف التنبيه');
            btnDel.innerHTML =
                '<i class="fa-solid fa-trash-can" aria-hidden="true"></i><span>حذف</span>';
            btnDel.addEventListener('click', function () {
                deleteAlert(a.alert_id);
            });
            row.appendChild(span);
            row.appendChild(sel);
            row.appendChild(btn);
            row.appendChild(btnDel);
            card.appendChild(h);
            card.appendChild(meta);
            card.appendChild(desc);
            if (a.reasons_text) {
                card.appendChild(reasons);
            }
            card.appendChild(row);
            box.appendChild(card);
        });
    } catch (e) {
        if (window.showToast) {
            window.showToast('تعذر تحميل التنبيهات', 'danger');
        }
    }
}

async function updateAlertStatus(alertId, newStatus) {
    try {
        const res = await fetch('/api/alert/update', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ alert_id: alertId, status: newStatus }),
        });
        const data = await res.json();
        if (!data.ok) {
            if (window.showToast) {
                window.showToast(data.message || 'فشل التحديث', 'danger');
            }
            return;
        }
        if (window.showToast) {
            window.showToast('تم تحديث حالة التنبيه', 'success');
        }
        loadAlerts();
        if (typeof window.refreshHeaderStats === 'function') {
            window.refreshHeaderStats();
        }
    } catch (e) {
        if (window.showToast) {
            window.showToast('خطأ في الشبكة', 'danger');
        }
    }
}

function filterAlerts() {
    loadAlerts();
}

let lastHighNew = null;

async function pollHighSeverity() {
    try {
        const res = await fetch('/api/alerts/summary');
        const data = await res.json();
        if (!data.ok) {
            return;
        }
        const h = data.high_new || 0;
        if (lastHighNew !== null && h > lastHighNew) {
            if (window.showToast) {
                window.showToast('تنبيه: يوجد تنبيه عالي الخطورة جديد يتطلب الانتباه', 'danger');
            }
        }
        lastHighNew = h;
    } catch (e) {}
}

document.addEventListener('DOMContentLoaded', function () {
    loadAlerts();
    const b = document.getElementById('applyFiltersBtn');
    if (b) {
        b.addEventListener('click', filterAlerts);
    }
    setInterval(loadAlerts, 60000);
    setInterval(pollHighSeverity, 60000);
    pollHighSeverity();
});
