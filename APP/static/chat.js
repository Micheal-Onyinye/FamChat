
const socket = io(); 
let currentChatType = window.initialChatType;
let currentChatId = window.initialChatId ? JSON.parse(window.initialChatId) : null; 

// Define receiverId and groupId based on initial chat state
let receiverId = currentChatType === 'user' ? currentChatId : null;
let groupId = currentChatType === 'group' ? currentChatId : null;

// New variable to store the Socket.IO room ID.
let currentChatRoomId = null;

const chatBox = document.getElementById('chat-box');
const messageInput = document.getElementById('message-input');
const emojiButton = document.querySelector('#emoji-button');
const messageForm = document.getElementById('message-form');
const userListElement = document.getElementById('user-list');
const groupListElement = document.getElementById('group-list');

// --- Added for displaying current chat partner/group ---
const chatWithElement = document.getElementById('chat-with');
const currentUserId = JSON.parse(window.currentUserId); 


// Emoji Picker setup (EmojiButton should now be globally available)
const picker = new EmojiButton(); 
picker.on('emoji', emoji => {
    messageInput.value += emoji.emoji;
});
if (emojiButton) { // Added a check to ensure emojiButton exists
    emojiButton.addEventListener('click', () => picker.togglePicker(emojiButton));
}


// --- New: Socket.IO Event Listeners ---


socket.on('connect', function() {
    console.log('Connected to Socket.IO server!');
    if (currentChatType && currentChatId) {
        calculateAndJoinRoom(currentChatType, currentChatId);
    }
});

socket.on('new_message', function(message) {
    console.log('New message received:', message);

    let messageBelongsToCurrentChat = false;

    if (currentChatType === 'user' && message.receiver_id !== null) {
        // For private chat, check if both current user and current chat partner are involved
        const participants1 = [parseInt(message.sender_id), parseInt(message.receiver_id)].sort().join('_');
        const participants2 = [parseInt(currentUserId), parseInt(currentChatId)].sort().join('_');
        if (participants1 === participants2) {
            messageBelongsToCurrentChat = true;
        }
    } else if (currentChatType === 'group' && message.group_id !== null) {
        // For group chat, simply check if the group ID matches
        if (parseInt(message.group_id) === parseInt(currentChatId)) {
            messageBelongsToCurrentChat = true;
        }
    }

    if (messageBelongsToCurrentChat) {
        addMessageToChatBox(message);
    }
});


messageForm.addEventListener('submit', function(event) {
    event.preventDefault();
    const content = messageInput.value.trim();
    if (!content) return;

    if (currentChatRoomId && currentChatRoomId !== "None" && currentChatRoomId !== "null") {
        const data = {
            message: content,
            receiver_id: currentChatType === 'user' ? parseInt(currentChatId) : null,
            group_id: currentChatType === 'group' ? parseInt(currentChatId) : null
        };
        
        socket.emit('send_message', data); 
        messageInput.value = '';
        
    } else {
        console.warn("Cannot send message: No chat selected or room not established.");
        flashMessage("Please select a chat to send messages.", "warning"); 
    }
});



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
        if (msg.is_current_user_sender) {
            div.style.textAlign = 'right';
        } else {
            div.style.textAlign = 'left';
        }
        div.innerHTML = `<strong>${msg.sender}</strong>: ${msg.content} <span class="timestamp">(${msg.timestamp})</span>`;
        fragment.appendChild(div);
    });

    chatBox.appendChild(fragment);
    chatBox.scrollTop = chatBox.scrollHeight;
}

function addMessageToChatBox(message) {
    const messageDiv = document.createElement('div');
    const isSentByCurrentUser = parseInt(message.sender_id) === parseInt(currentUserId);
    messageDiv.classList.add('message', isSentByCurrentUser ? 'sent-message' : 'received-message');

    const senderName = isSentByCurrentUser ? 'You' : message.sender_username; 
    
    messageDiv.innerHTML = `
        <div><strong>${senderName}:</strong> ${message.content}</div>
        <span class="timestamp">${message.timestamp}</span>
    `;
    chatBox.appendChild(messageDiv);
    scrollToBottom();
}

function calculateAndJoinRoom(type, id) {
    if (currentChatRoomId && currentChatRoomId !== "None" && currentChatRoomId !== "null") {
        socket.emit('leave_chat', { room_id: currentChatRoomId });
        console.log(`Left room: ${currentChatRoomId}`);
    }

    currentChatType = type;
    currentChatId = parseInt(id); 

    // Calculate new room ID
    if (type === 'user') {
        currentChatRoomId = String(Math.min(parseInt(currentUserId), currentChatId)) + '_' + String(Math.max(parseInt(currentUserId), currentChatId));
    } else if (type === 'group') {
        currentChatRoomId = 'group_' + String(currentChatId);
    } else {
        currentChatRoomId = null;
    }

    // Join the new room
    if (currentChatRoomId) {
        socket.emit('join_chat', { room_id: currentChatRoomId });
        console.log(`Joined new room: ${currentChatRoomId}`);
    }
}


function setActiveChat(type, id, name) {
    if (type === 'user') {
        receiverId = parseInt(id); 
        groupId = null;
        chatWithElement.textContent = name;
    } else if (type === 'group') {
        groupId = parseInt(id); 
        receiverId = null;
        chatWithElement.textContent = name + " (Group)";
    }

    calculateAndJoinRoom(type, id); 
    loadMessages(); 
}


// --- Initial Setup on DOM Content Loaded ---
document.addEventListener('DOMContentLoaded', () => {
    
    if (userListElement) {
        userListElement.addEventListener('click', (event) => {
            const clickedLink = event.target.closest('a[data-chat-type="user"]');
            if (clickedLink) {
                const userId = clickedLink.dataset.chatId;
                const userName = clickedLink.dataset.chatName;
                setActiveChat('user', userId, userName); 
                event.preventDefault(); 
                updateSidebarActiveState(clickedLink); 
            }
        });
    }

    if (groupListElement) {
        groupListElement.addEventListener('click', (event) => {
            const clickedLink = event.target.closest('a[data-chat-type="group"]');
            if (clickedLink) {
                const grpId = clickedLink.dataset.chatId;
                const groupName = clickedLink.dataset.chatName;
                setActiveChat('group', grpId, groupName || "Group Chat"); 
                event.preventDefault(); 
                updateSidebarActiveState(clickedLink); 
            }
        });
    }


    if (window.initialChatType && window.initialChatId !== 'null' && window.initialChatId !== '') {
        let initialChatTitle = document.getElementById('chat-with').textContent;
        setActiveChat(window.initialChatType, window.initialChatId, initialChatTitle);
    }

    scrollToBottom();
});


function flashMessage(message, category) {
    const flashContainer = document.querySelector('.flash-messages'); 
    if (!flashContainer) {
        console.warn("Flash message container not found. Message:", message);
        return;
    }
    const alertDiv = document.createElement('div');
    alertDiv.classList.add('alert', `alert-${category}`, 'alert-dismissible', 'fade', 'show');
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="close" data-dismiss="alert" aria-label="Close">
            <span aria-hidden="true">&times;</span>
        </button>
    `;
    flashContainer.appendChild(alertDiv);
    setTimeout(() => alertDiv.remove(), 5000);
}

// Helper to update the active class in the sidebar
function updateSidebarActiveState(clickedLink) {
    document.querySelectorAll('#user-list li, #group-list li').forEach(item => {
        item.classList.remove('active');
    });
    clickedLink.closest('li').classList.add('active');
}

// Helper to scroll chat box to bottom
function scrollToBottom() {
    chatBox.scrollTop = chatBox.scrollHeight;
}