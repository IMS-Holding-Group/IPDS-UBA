async function deleteActivity(activityId) {
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
            } else {
                alert(data.message || 'فشل الحذف');
            }
            return;
        }
        if (window.showToast) {
            window.showToast('تم حذف السجل', 'success');
        }
        window.location.reload();
    } catch (e) {
        if (window.showToast) {
            window.showToast('خطأ في الشبكة', 'danger');
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-delete-activity]').forEach(function (btn) {
        btn.addEventListener('click', function () {
            var id = parseInt(btn.getAttribute('data-delete-activity'), 10);
            if (id) {
                deleteActivity(id);
            }
        });
    });
    var exportBtn = document.getElementById('exportBtn');
    if (exportBtn) {
        exportBtn.addEventListener('click', function () {
            alert('تم التصدير (وظيفة تجريبية للعرض)');
        });
    }
});
