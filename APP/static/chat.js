import { EmojiButton } from '@joeattardi/emoji-button';

const socket = io(); 

// Correctly initialize currentChatType and currentChatId from window variables
let currentChatType = window.initialChatType || null; 
let currentChatId = window.initialChatId ? parseInt(window.initialChatId) : null; 

// Initial value for receiverId and groupId based on initial chat state
let receiverId = (currentChatType === 'user' && currentChatId) ? currentChatId : null;
let groupId = (currentChatType === 'group' && currentChatId) ? currentChatId : null;

// New variable to store the Socket.IO room ID.
let currentChatRoomId = null;

const chatBox = document.getElementById('chat-box');
const messageInput = document.getElementById('message-input');
const emojiButton = document.getElementById('emoji-button'); 
const messageForm = document.getElementById('message-form');
const userListElement = document.getElementById('user-list');
const groupListElement = document.getElementById('group-list');

const chatWithElement = document.getElementById('chat-with');
// Ensure currentUserId is parsed as an integer for reliable comparisons
const currentUserId = parseInt(window.currentUserId); 

// Emoji Picker setup
let picker;
// Check if EmojiButton is defined before trying to initialize it
if (typeof EmojiButton !== 'undefined') { 
    picker = new EmojiButton(); 
    picker.on('emoji', emoji => {
        messageInput.value += emoji.emoji;
    });
    if (emojiButton) {
        emojiButton.addEventListener('click', () => picker.togglePicker(emojiButton));
    }
} else {
    console.error("EmojiButton library not loaded. Check the CDN link in chat.html and ensure 'type=\"module\"' is correctly set if using ES modules for EmojiButton.");
}


// --- Socket.IO Event Listeners ---

socket.on('connect', function() {
    console.log('Connected to Socket.IO server!');
    // If an initial chat is set from Flask, join its room immediately
    // This ensures the client joins the correct room upon connection or refresh
    if (currentChatType && currentChatType !== 'null' && currentChatId) {
        calculateAndJoinRoom(currentChatType, currentChatId);
    }
});

socket.on('new_message', function(message) {
    console.log('New message received from server (Socket.IO):', message);
    console.log('Timestamp received in new_message:', message.timestamp); // ADDED DEBUG LOG

    let messageBelongsToCurrentChat = false;

    if (currentChatType === 'user' && message.receiver_id !== null && message.group_id === null) {

        const participantsInMsg = [parseInt(message.sender_id), parseInt(message.receiver_id)].sort().join('_');
        const participantsInCurrentChat = [currentUserId, currentChatId].sort().join('_');
        if (participantsInMsg === participantsInCurrentChat) {
            messageBelongsToCurrentChat = true;
        }
    } else if (currentChatType === 'group' && message.group_id !== null) {
        if (parseInt(message.group_id) === currentChatId) {
            messageBelongsToCurrentChat = true;
        }
    }

    if (messageBelongsToCurrentChat) {
        addMessageToChatBox(message);
    }
});


messageForm.addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent default form submission (page reload)
    const content = messageInput.value.trim();
    if (!content) return; // Don't send empty messages

    // Ensure a chat room is active before emitting a message
    if (currentChatRoomId && currentChatRoomId !== "null") { 
        const data = {
            message: content,
            // Set receiver_id or group_id based on the active chat type
            receiver_id: currentChatType === 'user' ? currentChatId : null,
            group_id: currentChatType === 'group' ? currentChatId : null
        };
        
        // Emit the message data to the server via Socket.IO
        socket.emit('send_message', data); 
        messageInput.value = ''; // Clear input field after sending
        
    } else {
        console.warn("Cannot send message: No chat selected or Socket.IO room not established.");
        flashMessage("Please select a chat to send messages.", "warning"); 
    }
});


// Function to add a single message to the chat box DOM
function addMessageToChatBox(message) {
    const chatBox = document.getElementById('chat-box');
    if (!chatBox) {
        console.error("Chat box element not found!");
        return;
    }

    const messageBubble = document.createElement('div');
    messageBubble.classList.add('message-bubble');

    messageBubble.classList.add(parseInt(message.sender_id) === currentUserId ? 'mine' : 'theirs');

    const messageHeader = document.createElement('div');
    messageHeader.classList.add('message-header');

    const senderUsername = document.createElement('span');
    senderUsername.classList.add('sender-username');
    senderUsername.textContent = (parseInt(message.sender_id) === currentUserId) ? 'You' : message.sender_username; 

    const timestamp = document.createElement('span');
    timestamp.classList.add('timestamp');
    
    const localTime = new Date(message.timestamp);  
    timestamp.textContent = localTime.toLocaleString('en-NG', {
        hour: 'numeric',
        minute: 'numeric',
        hour12: true,
        month: 'short',
        day: 'numeric'
    }); 
    console.log('Timestamp being assigned in addMessageToChatBox:', message.timestamp); // ADDED DEBUG LOG

    messageHeader.appendChild(senderUsername);
    messageHeader.appendChild(timestamp);
    
    const messageContent = document.createElement('div');
    messageContent.classList.add('message-content');
    messageContent.textContent = message.content; // Display the message content

    messageBubble.appendChild(messageHeader);
    messageBubble.appendChild(messageContent);
    chatBox.appendChild(messageBubble); 
    scrollToBottom(); 
}

// Function to calculate and join/leave Socket.IO rooms
function calculateAndJoinRoom(type, id) {
    if (currentChatRoomId && currentChatRoomId !== "null") {
        socket.emit('leave_chat', { room_id: currentChatRoomId });
        console.log(`Left room: ${currentChatRoomId}`);
    }

    currentChatType = type;
    currentChatId = parseInt(id); 

    if (type === 'user') {
        currentChatRoomId = String(Math.min(currentUserId, currentChatId)) + '_' + String(Math.max(currentUserId, currentChatId));
    } else if (type === 'group') {
        currentChatRoomId = 'group_' + String(currentChatId);
    } else {
        currentChatRoomId = null; 
    }

    if (currentChatRoomId) {
        socket.emit('join_chat', { room_id: currentChatRoomId });
        console.log(`Joined new room: ${currentChatRoomId}`);
    }
}

async function setActiveChat(type, id, name) {
    if (type === 'user') {
        receiverId = parseInt(id); 
        groupId = null;
    } else if (type === 'group') {
        groupId = parseInt(id); 
        receiverId = null;
    }
    chatWithElement.textContent = name; 

    chatBox.innerHTML = ''; 
    
    calculateAndJoinRoom(type, id); 

    try {
        const response = await fetch(`/api/messages/${type}/${id}`);
        if (!response.ok) { 
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const messages = await response.json(); 
        
        messages.forEach(message => {
            addMessageToChatBox(message); 
        });
    } catch (error) {
        console.error('Error fetching historical messages:', error);
        flashMessage('Failed to load past messages.', 'danger'); 
    }
    scrollToBottom(); 
}

// --- Initial Setup on DOM Content Loaded ---
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.chat-link').forEach(link => {
        link.addEventListener('click', (event) => {
            event.preventDefault(); 
            const chatType = link.dataset.chatType;
            const chatId = link.dataset.chatId;
            const chatName = link.dataset.chatName;
            setActiveChat(chatType, chatId, chatName); 
            updateSidebarActiveState(link); 
        });
    });

    if (window.initialMessages && Array.isArray(window.initialMessages) && window.initialMessages.length > 0) {
        console.log('DOM Content Loaded: Processing initialMessages from Flask.'); 
        window.initialMessages.forEach(message => {
            addMessageToChatBox(message); 
        });
    } else {
        console.log('DOM Content Loaded: No initialMessages or array is empty.');
        if (window.initialChatTitle && window.initialChatTitle !== "No Chat Selected") {
            chatWithElement.textContent = window.initialChatTitle;
        }
    }

    scrollToBottom();
    
    
    const currentActiveChatLink = document.querySelector(`.chat-link[data-chat-type="${window.initialChatType}"][data-chat-id="${window.initialChatId}"]`);
    if (currentActiveChatLink) {
        updateSidebarActiveState(currentActiveChatLink);
    }
});

function flashMessage(message, category) {
    const flashContainer = document.querySelector('.flash-messages'); 
    if (!flashContainer) {
        console.warn("Flash message container not found. Creating a temporary one. Message:", message);
        const body = document.querySelector('body');
        const container = document.createElement('div');
        container.classList.add('flash-messages', 'container', 'mt-3');
        body.insertBefore(container, body.firstChild);
        flashContainer = container; 
    }
    const alertDiv = document.createElement('div');
    alertDiv.classList.add('alert', `alert-${category}`, 'alert-dismissible', 'fade', 'show');
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    flashContainer.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 5000);
}

function updateSidebarActiveState(clickedLink) {
    document.querySelectorAll('.user-list-section ul li, .group-list-section ul li').forEach(item => {
        item.classList.remove('active'); 
    });
    clickedLink.closest('li').classList.add('active');
}

function scrollToBottom() {
    chatBox.scrollTop = chatBox.scrollHeight;
}
