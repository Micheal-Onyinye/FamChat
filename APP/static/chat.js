const chatBox = document.getElementById('chat-box');
const messageInput = document.getElementById('message-input');
const emojiButton = document.querySelector('#emoji-button');

const picker = new EmojiButton();
picker.on('emoji', emoji => {
    messageInput.value += emoji;
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
    }
}

async function loadMessages() {
    if (!window.receiverId) return;

    let url = `/get_messages?receiver_id=${window.receiverId}`;

    const response = await fetch(url);
    if (response.ok) {
        const data = await response.json();
        chatBox.innerHTML = '';
        data.messages.forEach(msg => {
            const div = document.createElement('div');
            div.className = 'message';
            div.innerHTML = `<strong>${msg.sender}</strong>: ${msg.content} <span class="timestamp">(${msg.timestamp})</span>`;
            chatBox.appendChild(div);
        });
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

setInterval(loadMessages, 5000);
window.onload = function() {
    // optionally preload first user
};
