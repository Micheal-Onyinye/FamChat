import { EmojiButton } from 'https://cdn.jsdelivr.net/npm/@joeattardi/emoji-button@latest/dist/index.min.js';

// State variables, initialized from window properties set by Flask
let receiverId = window.initialChatType === 'user' ? window.initialChatId : null;
let groupId = window.initialChatType === 'group' ? window.initialChatId : null;

const chatBox = document.getElementById('chat-box');
const messageInput = document.getElementById('message-input');
const emojiButton = document.querySelector('#emoji-button');
const messageForm = document.getElementById('message-form');
const userListElement = document.getElementById('user-list');
const groupListElement = document.getElementById('group-list'); // NEW: Get group list element


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
        await loadMessages();  // Wait for messages to load before scrolling
    } else {
        console.error('Failed to send message:', await response.text());
        alert('Message failed to send.');
    }
}

// Unified Load Message Handler
async function loadMessages() {
    chatBox.innerHTML = ''; // Clear existing messages

    let url = '';
    if (groupId) {
        url = `/get_group_messages/${groupId}`;
    } else if (receiverId) {
        url = `/get_messages?receiver_id=${receiverId}`;
    } else {
        return; // No chat selected, nothing to load
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
        // Use window.currentUserId for comparison, not msg.is_current_user_sender if it's not directly passed
        // However, the Flask view now correctly calculates and passes `is_current_user_sender`
        div.classList.add(msg.is_current_user_sender ? 'sent-message' : 'received-message');

        // You can make these styles more robust in your CSS (e.g., .sent-message and .received-message)
        // For demonstration, adding inline styles
        if (msg.is_current_user_sender) {
            div.style.textAlign = 'right'; // For sent messages
        } else {
            div.style.textAlign = 'left'; // For received messages
        }

        div.innerHTML = `<strong>${msg.sender}</strong>: ${msg.content} <span class="timestamp">(${msg.timestamp})</span>`;
        fragment.appendChild(div);
    });

    chatBox.appendChild(fragment);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Function to set the active chat
function setActiveChat(type, id, name) {
    if (type === 'user') {
        receiverId = id;
        groupId = null;
        document.getElementById('chat-with').textContent = name;
    } else if (type === 'group') {
        groupId = id;
        receiverId = null;
        document.getElementById('chat-with').textContent = name + " (Group)";
    }
    loadMessages();
}


// Initial Setup on DOM Content Loaded
document.addEventListener('DOMContentLoaded', () => {
    if (messageForm) {
        messageForm.addEventListener('submit', sendMessage);
    }

    // Event listener for private chat links (delegated to userListElement)
    if (userListElement) {
        userListElement.addEventListener('click', (event) => {
            const clickedLink = event.target.closest('a[data-chat-type="user"]');
            if (clickedLink) {
                const userId = clickedLink.dataset.chatId;
                const userName = clickedLink.dataset.chatName;
                setActiveChat('user', userId, userName);
                event.preventDefault(); // Prevent default link behavior
            }
        });
    }

    // Event listener for group chat links (delegated to groupListElement)
    if (groupListElement) { // Use the new groupListElement
        groupListElement.addEventListener('click', (event) => {
            const clickedLink = event.target.closest('a[data-chat-type="group"]');
            if (clickedLink) {
                const groupId = clickedLink.dataset.chatId;
                const groupName = clickedLink.dataset.chatName;
                setActiveChat('group', groupId, groupName || "Group Chat");
                event.preventDefault(); // Prevent default link behavior
            }
        });
    }

    // Load messages if initial chat is set by Flask
    if (window.initialChatType && window.initialChatId) {
        setActiveChat(window.initialChatType, window.initialChatId, document.getElementById('chat-with').textContent);
    }
});

// Expose setActiveChat globally if needed, though event delegation is better
// window.startChat = setActiveChat; // You can uncomment this if you need to call it from other inline JS (less ideal)