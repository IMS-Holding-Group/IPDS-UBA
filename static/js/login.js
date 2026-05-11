let keyTimestamps = [];
let lastKeyTime = null;

const pwd = document.getElementById('password');
if (pwd) {
    pwd.addEventListener('keydown', function () {
        const now = Date.now();
        if (lastKeyTime) {
            keyTimestamps.push(now - lastKeyTime);
            if (keyTimestamps.length > 40) {
                keyTimestamps.shift();
            }
        }
        lastKeyTime = now;
    });
}

function getAvgTypingSpeed() {
    if (keyTimestamps.length === 0) {
        return 5.0;
    }
    const avgInterval = keyTimestamps.reduce(function (a, b) {
        return a + b;
    }, 0) / keyTimestamps.length;
    if (avgInterval <= 0) {
        return 5.0;
    }
    return Math.round((1000 / avgInterval) * 10) / 10;
}

function showError(msg) {
    const el = document.getElementById('clientError');
    const srv = document.getElementById('serverError');
    if (srv) {
        srv.style.display = 'none';
    }
    if (el) {
        el.style.display = 'flex';
        el.textContent = msg;
    } else {
        alert(msg);
    }
}

function showSuspiciousAlert(msg) {
    const text =
        'تم رصد سلوك غير معتاد. التفاصيل: ' +
        (msg || '') +
        '\n\nهل تريد المتابعة إلى لوحة التحكم؟';
    if (window.confirm(text)) {
        window.location.href = '/dashboard';
    } else {
        window.location.href = '/logout';
    }
}

async function handleLogin(e) {
    e.preventDefault();
    const typingSpeed = getAvgTypingSpeed();
    const loginHour = new Date().getHours();
    const usernameEl = document.getElementById('username');
    const passwordEl = document.getElementById('password');
    const formData = {
        username: usernameEl ? usernameEl.value : '',
        password: passwordEl ? passwordEl.value : '',
        typing_speed: typingSpeed,
        login_hour: loginHour,
        url_address: window.location.href,
        session_duration: 0,
    };
    try {
        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData),
        });
        const data = await response.json();
        if (data.success) {
            if (data.suspicious) {
                showSuspiciousAlert(data.alert_message || 'يرجى الحذر والتحقق من الجهة المستهدفة.');
            } else {
                window.location.href = '/dashboard';
            }
        } else {
            showError(data.message || 'فشل تسجيل الدخول');
        }
    } catch (err) {
        showError('تعذر الاتصال بالخادم');
    }
}

const form = document.getElementById('loginForm');
if (form) {
    form.addEventListener('submit', handleLogin);
}
