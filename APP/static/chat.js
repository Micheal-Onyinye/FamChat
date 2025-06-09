import { EmojiButton } from 'https://cdn.jsdelivr.net/npm/@joeattardi/emoji-button@latest/dist/index.min.js';

let receiverId = null;
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

async function sendMessage(event) {
    event.preventDefault();
    const content = messageInput.value.trim();
    if (!content || !window.receiverId) return;

    const payload = {
        content: content,
        receiver_id: window.receiverId
    };

    const response = await fetch('/send_message', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    });

    if (response.ok) {
        messageInput.value = '';
        loadMessages();
    } else {
        console.error('Failed to send message:', response.status, await response.text());
        alert('Could not send message. Please try again!');
    }
}

async function loadMessages() {
    if (!window.receiverId) return;

    let url = `/get_messages?receiver_id=${window.receiverId}`;

    const response = await fetch(url);
    if (response.ok) {
        const data = await response.json();
        const fragment = document.createDocumentFragment();
        data.messages.forEach(msg => {
            const div = document.createElement('div');
            // --- MODIFIED LINE ---
            div.className = 'message'; 
            if (msg.is_current_user_sender) {
                div.classList.add('sent-message'); // Add a class for sent messages
            } else {
                div.classList.add('received-message'); // Add a class for received messages
            }
            // --- END MODIFIED LINE ---
            
            div.innerHTML = `<strong>${msg.sender}</strong>: ${msg.content} <span class="timestamp">(${msg.timestamp})</span>`;
            fragment.appendChild(div);
        });
        
        chatBox.innerHTML = '';
        chatBox.appendChild(fragment);

        chatBox.scrollTop = chatBox.scrollHeight;
    } else {
        console.error('Failed to load messages:', response.status, await response.text());
    }
}


function startChat(id, name) {
    receiverId = id;
    window.receiverId = id;
    document.getElementById('chat-with').textContent = name;
    loadMessages();
}

document.addEventListener('DOMContentLoaded', () => {
    if (messageForm) {
        messageForm.addEventListener('submit', sendMessage);
    }

    if (userListElement) {
        userListElement.addEventListener('click', (event) => {
            const clickedLink = event.target.closest('a');
            if (clickedLink && clickedLink.dataset.userId && clickedLink.dataset.userName) {
                const userId = clickedLink.dataset.userId;
                const userName = clickedLink.dataset.userName;
                startChat(userId, userName);
                event.preventDefault();
            }
        });
    }
});

