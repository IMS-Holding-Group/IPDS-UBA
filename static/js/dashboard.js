function drawActivityChart(data) {
    const canvas = document.getElementById('activityChart');
    if (!canvas || !canvas.getContext) {
        return;
    }
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, w, h);
    const pad = 36;
    const chartW = w - pad * 2;
    const chartH = h - pad * 2;
    const items = Array.isArray(data) ? data : [];
    const maxVal = items.reduce(function (m, d) {
        return Math.max(m, (d.normal || 0) + (d.suspicious || 0));
    }, 1);

    function xAt(i) {
        if (items.length <= 1) {
            return pad + chartW / 2;
        }
        return pad + (chartW * i) / (items.length - 1);
    }

    ctx.strokeStyle = '#d1d8e0';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(pad, pad);
    ctx.lineTo(pad, pad + chartH);
    ctx.lineTo(pad + chartW, pad + chartH);
    ctx.stroke();

    ctx.font = '600 12px IBM Plex Sans Arabic, sans-serif';
    ctx.fillStyle = '#5a6a7a';
    ctx.textAlign = 'center';
    items.forEach(function (d, i) {
        const label = (d.date || '').slice(5);
        ctx.fillText(label, xAt(i), h - 10);
    });

    function drawSeries(getter, color) {
        ctx.strokeStyle = color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        items.forEach(function (d, i) {
            const v = getter(d) || 0;
            const y = pad + chartH - (v / maxVal) * chartH;
            const x = xAt(i);
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        });
        ctx.stroke();
    }

    drawSeries(function (d) {
        return d.normal;
    }, '#2563a8');
    drawSeries(function (d) {
        return d.suspicious;
    }, '#c0392b');
}

async function loadStats() {
    try {
        const res = await fetch('/api/stats');
        const data = await res.json();
        if (!data.ok) {
            return;
        }
        const el1 = document.getElementById('statTotalActivities');
        if (el1) {
            el1.textContent = String(data.total_activities || 0);
        }
        const el2 = document.getElementById('statActiveAlerts');
        if (el2) {
            el2.textContent = String(data.active_alerts || 0);
        }
        const el3 = document.getElementById('statSecurityRate');
        if (el3) {
            el3.textContent = String(data.security_rate || 0) + '%';
        }
        const el4 = document.getElementById('statLastLogin');
        if (el4) {
            el4.textContent = window.formatDate ? window.formatDate(data.last_login) : data.last_login || '—';
        }
        drawActivityChart(data.chart || []);
    } catch (e) {}
}

async function deleteActivityById(activityId) {
    if (!confirm('حذف هذا السجل نهائياً؟')) {
        return;
    }
    try {
        const res = await fetch('/api/activities/delete', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ activity_id: activityId }),
        });
        const data = await res.json();
        if (!data.ok) {
            if (window.showToast) {
                window.showToast(data.message || 'فشل الحذف', 'danger');
            }
            return;
        }
        if (window.showToast) {
            window.showToast('تم حذف السجل', 'success');
        }
        loadRecentActivities();
        loadStats();
        if (typeof window.refreshHeaderStats === 'function') {
            window.refreshHeaderStats();
        }
    } catch (e) {
        if (window.showToast) {
            window.showToast('خطأ في الشبكة', 'danger');
        }
    }
}

async function loadRecentActivities() {
    try {
        const res = await fetch('/api/activities/recent?limit=10');
        const data = await res.json();
        const body = document.getElementById('recentActivitiesBody');
        if (!body || !data.ok) {
            return;
        }
        body.innerHTML = '';
        (data.items || []).forEach(function (row) {
            const tr = document.createElement('tr');
            const td1 = document.createElement('td');
            td1.textContent = window.formatDate ? window.formatDate(row.timestamp) : row.timestamp;
            const td2 = document.createElement('td');
            td2.textContent = row.activity_type || '';
            const td3 = document.createElement('td');
            td3.style.maxWidth = '260px';
            td3.style.wordBreak = 'break-all';
            td3.textContent = row.url_address || '—';
            const td4 = document.createElement('td');
            if (row.is_suspicious) {
                const b = document.createElement('span');
                b.className = 'badge badge-danger';
                b.textContent = 'مشبوه';
                td4.appendChild(b);
            } else {
                const b = document.createElement('span');
                b.className = 'badge badge-success';
                b.textContent = 'طبيعي';
                td4.appendChild(b);
            }
            const td5 = document.createElement('td');
            const delBtn = document.createElement('button');
            delBtn.type = 'button';
            delBtn.className = 'btn-delete-record';
            delBtn.title = 'حذف السجل';
            delBtn.setAttribute('aria-label', 'حذف السجل');
            delBtn.innerHTML =
                '<i class="fa-solid fa-trash-can" aria-hidden="true"></i><span>حذف</span>';
            delBtn.addEventListener('click', function () {
                deleteActivityById(row.activity_id);
            });
            td5.appendChild(delBtn);
            tr.appendChild(td1);
            tr.appendChild(td2);
            tr.appendChild(td3);
            tr.appendChild(td4);
            tr.appendChild(td5);
            body.appendChild(tr);
        });
    } catch (e) {}
}

async function analyzeURL() {
    const input = document.getElementById('urlAnalyze');
    const out = document.getElementById('analyzeResult');
    if (!input || !out) {
        return;
    }
    const url = (input.value || '').trim();
    if (!url) {
        out.innerHTML = '<span class="badge badge-warning">يرجى إدخال رابط</span>';
        return;
    }
    out.innerHTML = '<span style="font-weight:700;">جاري التحليل...</span>';
    try {
        const res = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                typing_speed: 5,
                login_hour: new Date().getHours(),
                failed_attempts: 0,
                session_duration: 300,
                url_address: url,
            }),
        });
        const data = await res.json();
        if (!data.ok) {
            out.innerHTML = '<span class="badge badge-danger">' + (data.message || 'خطأ') + '</span>';
            return;
        }
        const r = data.result || {};
        const conf = Math.round((r.confidence || 0) * 100);
        let html =
            '<div class="alert-banner ' +
            (r.is_suspicious ? 'warning' : 'success') +
            '">النتيجة: ' +
            (r.is_suspicious ? 'مشبوه' : 'طبيعي') +
            ' — درجة الثقة: ' +
            conf +
            '%</div>';
        if (r.description) {
            html += '<p style="margin-top:10px;font-weight:700;">' + r.description + '</p>';
        }
        if (r.reasons && r.reasons.length) {
            html += '<ul style="margin-top:8px;padding-right:18px;font-weight:600;">';
            r.reasons.forEach(function (x) {
                html += '<li>' + x + '</li>';
            });
            html += '</ul>';
        }
        out.innerHTML = html;
    } catch (e) {
        out.innerHTML = '<span class="badge badge-danger">تعذر الاتصال بالخادم</span>';
    }
}

document.addEventListener('DOMContentLoaded', function () {
    loadStats();
    loadRecentActivities();
    const btn = document.getElementById('analyzeUrlBtn');
    if (btn) {
        btn.addEventListener('click', analyzeURL);
    }
    setInterval(loadStats, 30000);
    setInterval(loadRecentActivities, 45000);
});
