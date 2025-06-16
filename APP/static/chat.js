import { EmojiButton } from 'https://cdn.jsdelivr.net/npm/@joeattardi/emoji-button@latest/dist/index.min.js';

// State
let receiverId = null;
let groupId = null;
window.receiverId = null;

const chatBox = document.getElementById('chat-box');
const messageInput = document.getElementById('message-input');
const emojiButton = document.querySelector('#emoji-button');
const messageForm = document.getElementById('message-form');
const userListElement = document.getElementById('user-list');

// Emoji Picker setup
const picker = new EmojiButton();
picker.on('emoji', emoji => {
    messageInput.value += emoji.emoji;
});
emojiButton.addEventListener('click', () => picker.togglePicker(emojiButton));

// Unified Send Message Handler
async function sendMessage(event) {
    event.preventDefault();
    const content = messageInput.value.trim();
    if (!content) return;

    let endpoint = '';
    let payload = { content };

    if (groupId) {
        endpoint = `/send_group_message/${groupId}`;
    } else if (receiverId) {
        endpoint = `/send_message`;
        payload.receiver_id = receiverId;
    } else {
        console.warn('No receiver or group selected.');
        return;
    }

    const response = await fetch(endpoint, {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });

    if (response.ok) {
        messageInput.value = '';
        loadMessages();  // Unified load
    } else {
        console.error('Failed to send message:', await response.text());
        alert('Message failed to send.');
    }
}

// Unified Load Message Handler
async function loadMessages() {
    chatBox.innerHTML = '';

    let url = '';
    if (groupId) {
        url = `/get_group_messages/${groupId}`;
    } else if (receiverId) {
        url = `/get_messages?receiver_id=${receiverId}`;
    } else {
        return;
    }

    const response = await fetch(url);
    if (!response.ok) {
        console.error('Failed to load messages:', await response.text());
        return;
    }

    const data = await response.json();
    const fragment = document.createDocumentFragment();

    data.messages.forEach(msg => {
        const div = document.createElement('div');
        div.className = 'message';
        div.classList.add(msg.is_current_user_sender ? 'sent-message' : 'received-message');

        div.innerHTML = `<strong>${msg.sender}</strong>: ${msg.content} <span class="timestamp">(${msg.timestamp})</span>`;
        fragment.appendChild(div);
    });

    chatBox.appendChild(fragment);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Private Chat Starter
function startChat(id, name) {
    receiverId = id;
    groupId = null;
    window.receiverId = id;
    document.getElementById('chat-with').textContent = `${name}`;
    loadMessages();
}

// Group Chat Starter
function startGroupChat(id, name = "Group Chat") {
    groupId = id;
    receiverId = null;
    window.receiverId = null;
    document.getElementById("chat-with").textContent = name;
    loadMessages();
}

// Initial Setup
document.addEventListener('DOMContentLoaded', () => {
    if (messageForm) {
        messageForm.addEventListener('submit', sendMessage);
    }

    if (userListElement) {
        userListElement.addEventListener('click', (event) => {
            const clickedLink = event.target.closest('a');
            if (!clickedLink) return;

            const userId = clickedLink.dataset.userId;
            const userName = clickedLink.dataset.userName;
            const groupIdAttr = clickedLink.dataset.groupId;
            const groupNameAttr = clickedLink.dataset.groupName;

            if (userId && userName) {
                startChat(userId, userName);
            } else if (groupIdAttr) {
                startGroupChat(groupIdAttr, groupNameAttr || "Group Chat");
            }

            event.preventDefault();
        });
    }
});
