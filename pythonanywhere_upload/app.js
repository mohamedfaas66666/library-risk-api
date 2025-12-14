// API Configuration - Same domain
const API_URL = '/api';

// State
let currentUser = null;

// Screen Navigation
function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(screenId).classList.add('active');
}

// Login Handler
async function handleLogin(event) {
    event.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const errorEl = document.getElementById('login-error');

    errorEl.textContent = 'جاري تسجيل الدخول...';

    try {
        const response = await fetch(`${API_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (data.success) {
            currentUser = { token: data.token, name: data.name };
            localStorage.setItem('user', JSON.stringify(currentUser));
            errorEl.textContent = '';
            showScreen('chat-screen');
        } else {
            errorEl.textContent = data.message || 'فشل تسجيل الدخول';
        }
    } catch (error) {
        errorEl.textContent = 'خطأ في الاتصال بالسيرفر';
    }
}

// Signup Handler
async function handleSignup(event) {
    event.preventDefault();
    const name = document.getElementById('signup-name').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    const errorEl = document.getElementById('signup-error');

    errorEl.textContent = 'جاري إنشاء الحساب...';

    try {
        const response = await fetch(`${API_URL}/signup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password })
        });

        const data = await response.json();

        if (data.success) {
            currentUser = { token: data.token, name: data.name };
            localStorage.setItem('user', JSON.stringify(currentUser));
            errorEl.textContent = '';
            showScreen('chat-screen');
        } else {
            errorEl.textContent = data.message || 'فشل إنشاء الحساب';
        }
    } catch (error) {
        errorEl.textContent = 'خطأ في الاتصال بالسيرفر';
    }
}

// Chat Functions
function handleKeyPress(event) {
    if (event.key === 'Enter') {
        sendMessage();
    }
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();

    if (!message) return;

    addMessage(message, false);
    input.value = '';

    const typingId = showTyping();

    try {
        const response = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message })
        });

        const data = await response.json();
        removeTyping(typingId);

        if (data.success) {
            addMessage(data.answer, true, data.category);
        } else {
            addMessage(data.message || 'عذراً، حدث خطأ', true);
        }
    } catch (error) {
        removeTyping(typingId);
        addMessage('عذراً، لا يمكن الاتصال بالسيرفر', true);
    }
}

function addMessage(text, isBot, category = '') {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${isBot ? 'bot-message' : 'user-message'}`;

    let categoryBadge = '';
    if (category && isBot) {
        categoryBadge = `<span class="category-badge">${category}</span>`;
    }

    const botAvatar = isBot ? `<div class="bot-avatar"><img src="1.png" alt="Bot"></div>` : '';

    messageDiv.innerHTML = `
        ${botAvatar}
        <div class="message-bubble">
            ${categoryBadge}
            <p>${text}</p>
        </div>
    `;

    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showTyping() {
    const messagesContainer = document.getElementById('chat-messages');
    const typingDiv = document.createElement('div');
    typingDiv.className = 'message bot-message';
    typingDiv.id = 'typing-' + Date.now();
    typingDiv.innerHTML = `
        <div class="bot-avatar"><img src="1.png" alt="Bot"></div>
        <div class="message-bubble">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    messagesContainer.appendChild(typingDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return typingDiv.id;
}

function removeTyping(id) {
    const typingEl = document.getElementById(id);
    if (typingEl) typingEl.remove();
}

function logout() {
    localStorage.removeItem('user');
    currentUser = null;
    showScreen('welcome-screen');
}

window.onload = function () {
    const savedUser = localStorage.getItem('user');
    if (savedUser) {
        currentUser = JSON.parse(savedUser);
        showScreen('chat-screen');
    }
};
