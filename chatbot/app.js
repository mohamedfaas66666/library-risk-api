// API URL - غيره للسيرفر بتاعك
const API_URL = '/api';

let currentUser = null;

// Screen Navigation
function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(screenId).classList.add('active');
}

// Login
async function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const errorEl = document.getElementById('login-error');

    errorEl.textContent = 'جاري تسجيل الدخول...';
    errorEl.style.color = '#667eea';

    try {
        const res = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();

        if (data.success) {
            currentUser = { token: data.token, name: data.name };
            localStorage.setItem('user', JSON.stringify(currentUser));
            errorEl.textContent = '';
            showScreen('chat-screen');
            showWelcome();
        } else {
            errorEl.style.color = '#e74c3c';
            errorEl.textContent = data.message || 'فشل تسجيل الدخول';
        }
    } catch (err) {
        errorEl.style.color = '#e74c3c';
        errorEl.textContent = 'خطأ في الاتصال بالسيرفر';
    }
}

// Signup
async function handleSignup(event) {
    event.preventDefault();
    const name = document.getElementById('signup-name').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    const errorEl = document.getElementById('signup-error');

    errorEl.textContent = 'جاري إنشاء الحساب...';
    errorEl.style.color = '#667eea';

    try {
        const res = await fetch(`${API_URL}/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        });
        const data = await res.json();

        if (data.success) {
            currentUser = { token: data.token, name: data.name };
            localStorage.setItem('user', JSON.stringify(currentUser));
            errorEl.textContent = '';
            showScreen('chat-screen');
            showWelcome();
        } else {
            errorEl.style.color = '#e74c3c';
            errorEl.textContent = data.message || 'فشل إنشاء الحساب';
        }
    } catch (err) {
        errorEl.style.color = '#e74c3c';
        errorEl.textContent = 'خطأ في الاتصال بالسيرفر';
    }
}

// Chat Functions
function handleKeyPress(event) {
    if (event.key === 'Enter') sendMessage();
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message) return;

    addMessage(message, 'user');
    input.value = '';

    const typingId = showTyping();

    try {
        const headers = { 'Content-Type': 'application/json' };
        if (currentUser?.token) {
            headers['Authorization'] = 'Bearer ' + currentUser.token;
        }

        const res = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers,
            body: JSON.stringify({ message })
        });
        const data = await res.json();

        removeTyping(typingId);

        if (data.success) {
            addMessage(data.answer, 'bot');
        } else {
            addMessage(data.message || 'حدث خطأ', 'bot');
        }
    } catch (err) {
        removeTyping(typingId);
        addMessage('لا يمكن الاتصال بالسيرفر', 'bot');
    }
}

function addMessage(text, type) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = `message ${type}`;
    div.innerHTML = `<div class="message-bubble">${text.replace(/\n/g, '<br>')}</div>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function showTyping() {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'message bot';
    div.id = 'typing-' + Date.now();
    div.innerHTML = `<div class="message-bubble"><div class="typing"><span></span><span></span><span></span></div></div>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div.id;
}

function removeTyping(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function showWelcome() {
    const container = document.getElementById('chat-messages');
    container.innerHTML = '';
    addMessage(`مرحباً ${currentUser?.name || ''}! 👋\nأنا شات بوت ذكي، اكتب لي أي سؤال وسأساعدك.`, 'bot');
}

function logout() {
    localStorage.removeItem('user');
    currentUser = null;
    document.getElementById('chat-messages').innerHTML = '';
    showScreen('welcome-screen');
}

// Auto Login
window.onload = function () {
    const saved = localStorage.getItem('user');
    if (saved) {
        currentUser = JSON.parse(saved);
        showScreen('chat-screen');
        showWelcome();
    }
};
