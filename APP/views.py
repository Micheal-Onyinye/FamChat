from flask import Blueprint, render_template,request, jsonify
from flask_login import login_required,current_user
from . import db
from .models import Message, User




views = Blueprint('views', __name__)
@views.route ('/home')
def home():
    return render_template('home.html')

@views.route('/chat')
@login_required
def chat():
    # Get all users except the current user
    users = User.query.filter(User.id != current_user.id).all()
    return render_template('chat.html', users=users, current_user=current_user)

@views.route('/send_message', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    content = data.get('content')
    group_id = data.get('group_id')     # for group chats
    receiver_id = data.get('receiver_id')  # for private chats

    if not content:
        return jsonify({'error': 'Empty message'}), 400

    if not group_id and not receiver_id:
        return jsonify({'error': 'No recipient specified'}), 400

    message = Message(
        content=content,
        sender_id=current_user.id,
        group_id=group_id,           # either this
        receiver_id=receiver_id      # or this
    )

    db.session.add(message)
    db.session.commit()

    return jsonify({'message': 'Message sent successfully'})


@views.route('/get_messages', methods=['GET'])
@login_required
def get_messages():
    group_id = request.args.get('group_id')
    receiver_id = request.args.get('receiver_id')  # For private chats

    if group_id:
        # Group messages
        messages = Message.query.filter_by(group_id=group_id).order_by(Message.timestamp).all()
    elif receiver_id:
        # Private chat: messages where current user is sender or receiver
        messages = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == receiver_id)) |
            ((Message.sender_id == receiver_id) & (Message.receiver_id == current_user.id))
        ).order_by(Message.timestamp).all()
    else:
        # Optional fallback
        messages = []

    formatted = [{
        'sender': msg.sender.username,
        'content': msg.content,
        'timestamp': msg.timestamp.strftime("%H:%M"),
    } for msg in messages]

    return jsonify({'messages': formatted})