const socket = io();

let currentUser = '';
let emojiOpen = false;
let typingTimeout = null;

const EMOJIS = [
    '😊','😂','😍','🤔','😎','👍','👏','🙏',
    '❤️','🔥','🎉','💯','😢','😡','🤣','😜',
    '🥳','😇','🤗','👋','✅','⭐','💪','🎓',
    '🚀','⚡','💻','📚','🏆','🌟','🎯','💡',
    '😤','🫡','🤝','🙌','💀','👀','🤩','😏',
    '🎶','☕','📌','🧠','💬','📸','🌈','✨'
];

// ===== DOM ELEMENTS =====
const loginScreen = document.getElementById('loginScreen');
const chatContainer = document.getElementById('chatContainer');
const usernameInput = document.getElementById('usernameInput');
const joinBtn = document.getElementById('joinBtn');
const messagesArea = document.getElementById('messagesArea');
const messageInput = document.getElementById('messageInput');
const sendBtn = document.getElementById('sendBtn');
const emojiBtn = document.getElementById('emojiBtn');
const emojiPicker = document.getElementById('emojiPicker');
const fileBtn = document.getElementById('fileBtn');
const imageBtn = document.getElementById('imageBtn');
const fileInput = document.getElementById('fileInput');
const imageInput = document.getElementById('imageInput');
const onlineCount = document.getElementById('onlineCount');
const statusText = document.getElementById('statusText');
const typingIndicator = document.getElementById('typingIndicator');
const typingUser = document.getElementById('typingUser');
const lightbox = document.getElementById('lightbox');
const lightboxImg = document.getElementById('lightboxImg');

// ===== LOGIN =====
joinBtn.addEventListener('click', joinChat);
usernameInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') joinChat();
});

function joinChat() {
    const name = usernameInput.value.trim();
    if (!name) {
        usernameInput.style.borderColor = '#ef4444';
        usernameInput.style.boxShadow = '0 0 0 3px rgba(239,68,68,0.15)';
        setTimeout(() => {
            usernameInput.style.borderColor = '';
            usernameInput.style.boxShadow = '';
        }, 1500);
        return;
    }
    currentUser = name;
    loginScreen.classList.add('hidden');
    setTimeout(() => {
        loginScreen.style.display = 'none';
        chatContainer.classList.add('active');
        messageInput.focus();
    }, 600);
    socket.emit('join', { username: name });
}

// ===== SEND MESSAGE =====
sendBtn.addEventListener('click', sendMessage);
messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

messageInput.addEventListener('input', () => {
    autoResize(messageInput);
    socket.emit('typing', {});
    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
        socket.emit('stop_typing', {});
    }, 1500);
});

function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
}

function sendMessage() {
    const msg = messageInput.value.trim();
    if (!msg) return;
    socket.emit('send_message', { message: msg });
    messageInput.value = '';
    autoResize(messageInput);
    socket.emit('stop_typing', {});
}

// ===== FILE / IMAGE =====
fileBtn.addEventListener('click', () => fileInput.click());
imageBtn.addEventListener('click', () => imageInput.click());

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 25 * 1024 * 1024) {
        addSystemMessage('File too large (max 25MB)');
        return;
    }
    const reader = new FileReader();
    reader.onload = () => {
        const base64 = reader.result.split(',')[1];
        socket.emit('send_file', {
            filename: file.name,
            data: base64,
            size: file.size
        });
    };
    reader.readAsDataURL(file);
    fileInput.value = '';
});

imageInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (file.size > 25 * 1024 * 1024) {
        addSystemMessage('Image too large (max 25MB)');
        return;
    }
    const reader = new FileReader();
    reader.onload = () => {
        const base64 = reader.result.split(',')[1];
        socket.emit('send_image', {
            filename: file.name,
            data: base64
        });
    };
    reader.readAsDataURL(file);
    imageInput.value = '';
});

// ===== EMOJI PICKER =====
emojiBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    emojiOpen = !emojiOpen;
    emojiPicker.classList.toggle('active', emojiOpen);
});

document.addEventListener('click', (e) => {
    if (emojiOpen && !emojiPicker.contains(e.target) && e.target !== emojiBtn) {
        emojiOpen = false;
        emojiPicker.classList.remove('active');
    }
});

function buildEmojiPicker() {
    const grid = emojiPicker.querySelector('.emoji-grid');
    EMOJIS.forEach(em => {
        const btn = document.createElement('button');
        btn.className = 'emoji-btn';
        btn.textContent = em;
        btn.addEventListener('click', () => {
            messageInput.value += em;
            messageInput.focus();
        });
        grid.appendChild(btn);
    });
}
buildEmojiPicker();

// ===== LIGHTBOX =====
lightbox.addEventListener('click', () => {
    lightbox.classList.remove('active');
});

function openLightbox(src) {
    lightboxImg.src = src;
    lightbox.classList.add('active');
}

// ===== SOCKET EVENTS =====
socket.on('message', (data) => {
    const isSent = data.username === currentUser;

    if (data.type === 'text') {
        addMessageBubble(data.username, data.message, data.timestamp, isSent);
    } else if (data.type === 'file') {
        addFileBubble(data.username, data.filename, data.size, data.timestamp, isSent);
    } else if (data.type === 'image') {
        addImageBubble(data.username, data.image_data, data.filename, data.timestamp, isSent);
    }
});

socket.on('user_joined', (data) => {
    addSystemMessage(`${data.username} joined the chat`);
    updateOnlineCount(data.count);
});

socket.on('user_left', (data) => {
    addSystemMessage(`${data.username} left the chat`);
    updateOnlineCount(data.count);
});

socket.on('user_typing', (data) => {
    typingUser.textContent = data.username;
    typingIndicator.classList.add('active');
});

socket.on('user_stop_typing', () => {
    typingIndicator.classList.remove('active');
});

socket.on('error', (data) => {
    addSystemMessage(`Error: ${data.message}`);
});

socket.on('disconnect', () => {
    addSystemMessage('Disconnected from server');
    statusText.textContent = 'Offline';
    document.querySelector('.status-dot').style.background = '#ef4444';
});

socket.on('connect', () => {
    if (currentUser) {
        statusText.textContent = `${currentUser} · Online`;
        document.querySelector('.status-dot').style.background = '#22c55e';
    }
});

// ===== RENDER HELPERS =====
function getInitials(name) {
    return name.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
}

function formatSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / 1048576).toFixed(1) + ' MB';
}

function addMessageBubble(username, message, time, isSent) {
    const div = document.createElement('div');
    div.className = `message ${isSent ? 'sent' : 'received'}`;
    div.innerHTML = `
        <div class="msg-avatar">${getInitials(username)}</div>
        <div class="msg-content">
            <div class="msg-sender">${escapeHtml(username)}</div>
            <div class="msg-bubble">${escapeHtml(message)}</div>
            <div class="msg-time">${time}</div>
        </div>
    `;
    messagesArea.appendChild(div);
    scrollToBottom();
}

function addFileBubble(username, filename, size, time, isSent) {
    const div = document.createElement('div');
    div.className = `message ${isSent ? 'sent' : 'received'}`;
    div.innerHTML = `
        <div class="msg-avatar">${getInitials(username)}</div>
        <div class="msg-content">
            <div class="msg-sender">${escapeHtml(username)}</div>
            <div class="msg-bubble file-bubble">
                <div class="file-info">
                    <div class="file-icon">📁</div>
                    <div class="file-details">
                        <div class="file-name">${escapeHtml(filename)}</div>
                        <div class="file-size">${formatSize(size)}</div>
                    </div>
                </div>
            </div>
            <div class="msg-time">${time}</div>
        </div>
    `;
    messagesArea.appendChild(div);
    scrollToBottom();
}

function addImageBubble(username, imageData, filename, time, isSent) {
    const ext = filename.split('.').pop().toLowerCase();
    const mime = ext === 'png' ? 'image/png' : ext === 'gif' ? 'image/gif' : 'image/jpeg';
    const src = `data:${mime};base64,${imageData}`;

    const div = document.createElement('div');
    div.className = `message ${isSent ? 'sent' : 'received'}`;
    div.innerHTML = `
        <div class="msg-avatar">${getInitials(username)}</div>
        <div class="msg-content">
            <div class="msg-sender">${escapeHtml(username)}</div>
            <div class="msg-bubble image-bubble">
                <img class="msg-image" src="${src}" alt="${escapeHtml(filename)}" onclick="openLightbox(this.src)">
            </div>
            <div class="msg-time">${time}</div>
        </div>
    `;
    messagesArea.appendChild(div);
    scrollToBottom();
}

function addSystemMessage(text) {
    const div = document.createElement('div');
    div.className = 'system-message';
    div.innerHTML = `<span>${escapeHtml(text)}</span>`;
    messagesArea.appendChild(div);
    scrollToBottom();
}

function updateOnlineCount(count) {
    onlineCount.textContent = count;
}

function scrollToBottom() {
    requestAnimationFrame(() => {
        messagesArea.scrollTop = messagesArea.scrollHeight;
    });
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
