from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timezone
import os
from dateutil import tz
from sqlalchemy import or_ 
from . import db, socketio 
from .models import Message, User, UpdateProfileForm, Group
from .forms import CreateGroupForm
from .utilis import save_profile_pic 
from werkzeug.utils import secure_filename

views = Blueprint('views', __name__)

LOCAL_TZ = tz.gettz('Africa/Lagos')
if not LOCAL_TZ:
    print("Warning: 'Africa/Lagos' timezone not found. Using system local time as fallback.")
    LOCAL_TZ = tz.tzlocal()


@views.route('/')
def index():
    """Redirects to the default chat view."""
    return redirect(url_for('views.chat_default'))

@views.route('/home')
def home():
    return render_template('home.html')

# NEW default /chat route
@views.route('/chat')
@login_required
def chat_default():
    general_chat = Group.query.filter_by(name="General Chat").first()
    if general_chat and current_user in general_chat.members:
        return redirect(url_for('views.chat_specific', chat_type='group', chat_id=general_chat.id))

    if current_user.groups.first():
        return redirect(url_for('views.chat_specific', chat_type='group', chat_id=current_user.groups.first().id))

    other_users = User.query.filter(User.id != current_user.id).all()
    if other_users:
        return redirect(url_for('views.chat_specific', chat_type='user', chat_id=other_users[0].id))
    
    flash("No active chats available. You can create a group or wait for others to register!", "info")
    return render_template('chat.html', 
                            users=User.query.filter(User.id != current_user.id).all(), 
                            groups=current_user.groups, 
                            current_user=current_user, 
                            chat_title="No Chat Selected", 
                            profile_pic='avatar.jpg', 
                            chat_type='null', # Pass 'null' string if no chat is active
                            chat_id='null', # Pass 'null' string if no chat is active
                            initial_messages=[], # Ensure it's an empty list
                            current_chat_room_id='null', # Pass 'null' if no chat is active
                            initial_chat_title="No Chat Selected", # <--- ADDED: For initial setup
                            cache_buster=datetime.now(timezone.utc).timestamp())


# Specific chat route (user or group)
@views.route('/chat/<string:chat_type>/<int:chat_id>') 
@login_required
def chat_specific(chat_type, chat_id):
    all_users = User.query.filter(User.id != current_user.id).all() 
    all_groups = current_user.groups 
    
    chat_title = ""
    profile_pic_filename = 'avatar.jpg'
    messages = []
    
    # NEW: Variable to hold the Socket.IO room ID for the current chat
    current_chat_room_id = None 

    if chat_type == 'user':
        chat_partner = User.query.get(chat_id)
        if chat_partner:
            chat_title = chat_partner.username
            profile_pic_filename = chat_partner.profile_pic if chat_partner.profile_pic else 'avatar.jpg'
            
            # Define a consistent room ID for private chats (sorted user IDs)
            current_chat_room_id = str(min(current_user.id, chat_partner.id)) + '_' + str(max(current_user.id, chat_partner.id))
            
            # Load initial private messages
            messages_db = Message.query.filter(
                or_(
                    (Message.sender_id == current_user.id) & (Message.receiver_id == chat_id),
                    (Message.sender_id == chat_id) & (Message.receiver_id == current_user.id)
                ),
                Message.group_id == None 
            ).order_by(Message.timestamp).all()
            
            for msg in messages_db:
                dt_utc = msg.timestamp if msg.timestamp.tzinfo else msg.timestamp.replace(tzinfo=timezone.utc)
                local_timestamp = dt_utc.astimezone(LOCAL_TZ)
                messages.append({
                    'sender_id': msg.sender.id, 
                    'sender_username': msg.sender.username,
                    'content': msg.content,
                    'timestamp': local_timestamp.strftime("%b %d, %I:%M %p"), 
                    'is_current_user_sender': msg.sender_id == current_user.id
                })
        else:
            flash("User not found.", "danger")
            return redirect(url_for('views.chat_default'))

    elif chat_type == 'group':
        group = Group.query.get(chat_id)
        if group and current_user in group.members:
            chat_title = group.name
            profile_pic_filename = group.profile_pic if group.profile_pic else 'avatar.jpg'
            
            # Consistent room ID for groups
            current_chat_room_id = 'group_' + str(group.id) 

            # Load initial group messages
            messages_db = Message.query.filter_by(group_id=group.id).order_by(Message.timestamp).all()
            for msg in messages_db:
                dt_utc = msg.timestamp if msg.timestamp.tzinfo else msg.timestamp.replace(tzinfo=timezone.utc)
                local_timestamp = dt_utc.astimezone(LOCAL_TZ)
                messages.append({
                    'sender_id': msg.sender.id, 
                    'sender_username': msg.sender.username,
                    'content': msg.content,
                    'timestamp': local_timestamp.strftime("%b %d, %I:%M %p"), 
                    'is_current_user_sender': msg.sender_id == current_user.id
                })
        else:
            flash("Group not found or you are not a member.", "danger")
            return redirect(url_for('views.chat_default'))
    else:
        flash("Invalid chat type.", "danger")
        return redirect(url_for('views.chat_default'))

    cache_buster = datetime.now(timezone.utc).timestamp()

    return render_template('chat.html',
                            users=all_users, 
                            groups=all_groups, 
                            chat_title=chat_title,
                            profile_pic=profile_pic_filename,
                            chat_type=chat_type, 
                            chat_id=chat_id, 
                            initial_messages=messages, 
                            current_user=current_user,
                            current_chat_room_id=current_chat_room_id,
                            initial_chat_title=chat_title, 
                            cache_buster=cache_buster)


@views.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        if form.profile_pic.data:
            try:
                pic_file = save_profile_pic(form.profile_pic.data)
                current_user.profile_pic = pic_file 
            except Exception as e:
                flash(f"Error uploading profile picture: {e}", 'danger')
                return redirect(url_for('views.profile')) 

        current_user.username = form.username.data
        db.session.commit()

        flash('Your profile has been updated!', 'success')
        return redirect(url_for('views.profile'))
    else:
        if request.method == 'POST':
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in {field}: {error}", 'danger')

    form.username.data = current_user.username
    cache_buster = datetime.now(timezone.utc).timestamp()
    return render_template('profile.html', form=form, cache_buster=cache_buster)


@views.route('/create-group', methods=['GET', 'POST'])
@login_required
def create_group():
    form = CreateGroupForm()
    form.members.choices = [(user.id, user.username) for user in User.query.filter(User.id != current_user.id).all()]
    
    group_pic = 'avatar.jpg'  # Default fallback image

    if form.validate_on_submit():
        file = request.files.get('profile_pic')
        if file and file.filename != '':
            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
            ext = file.filename.rsplit('.', 1)[1].lower()
            if '.' in file.filename and ext in allowed_extensions:
                upload_folder = os.path.join(current_app.root_path, 'static', 'profile_pic')
                os.makedirs(upload_folder, exist_ok=True)
                
                from datetime import datetime
                timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{timestamp_str}_{secure_filename(file.filename)}"

                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)

                group_pic = filename
            else:
                flash('Invalid file type for profile picture. Allowed: png, jpg, jpeg, gif', 'danger')
                return render_template('create_group.html', form=form, group_pic=group_pic)


        group = Group(
            name=form.name.data,
            description=form.description.data,
            profile_pic=group_pic,
            creator_id=current_user.id
        )

        db.session.add(group)

        group.members.append(current_user)
        for user_id in form.members.data:
            user = User.query.get(user_id)
            if user:
                group.members.append(user)

        db.session.commit()
        flash('Group created successfully!', 'success')
        return redirect(url_for('views.chat_default')) 

    return render_template('create_group.html', form=form, group_pic=group_pic)


@views.route('/delete-group/<int:group_id>', methods=['POST'])
@login_required
def delete_group(group_id):
    group = Group.query.get_or_404(group_id)

    if group.creator_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403

    Message.query.filter_by(group_id=group.id).delete()

    for member in group.members.all():
        group.members.remove(member)

    db.session.delete(group)
    db.session.commit()
    flash("Group deleted successfully", "success")
    return redirect(url_for('views.chat_default'))


# --- NEW: Socket.IO Event Handlers ---
from flask_socketio import emit, join_room, leave_room
from flask import request 

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        print(f"User {current_user.username} connected with sid: {request.sid}")
        join_room(f"user_{current_user.id}")
    else:
        print(f"Anonymous user connected with sid: {request.sid}. Disconnecting.")
        return False 

@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        print(f"User {current_user.username} disconnected with sid: {request.sid}")
        leave_room(f"user_{current_user.id}") # Leave personal room
    else:
        print(f"Anonymous user disconnected with sid: {request.sid}")


@socketio.on('join_chat')
@login_required
def handle_join_chat(data):
    
    room_id = data.get('room_id')
    if room_id:
        join_room(room_id)
        print(f'{current_user.username} joined room: {room_id}')
    else:
        print(f"Error: {current_user.username} tried to join a chat without a room_id.")

@socketio.on('leave_chat')
@login_required
def handle_leave_chat(data):
    
    room_id = data.get('room_id')
    if room_id:
        leave_room(room_id)
        print(f'{current_user.username} left room: {room_id}')
    else:
        print(f"Error: {current_user.username} tried to leave a chat without a room_id.")


@socketio.on('send_message')
@login_required
def handle_send_message(data):

    user_id = current_user.id
    receiver_id = data.get('receiver_id')
    group_id = data.get('group_id')
    message_content = data.get('message', '').strip()

    if not message_content:
        return 

    timestamp_utc = datetime.now(timezone.utc)
    new_message = Message(
        sender_id=user_id,
        content=message_content,
        timestamp=timestamp_utc 
    )

    room_id = None
    if receiver_id is not None: 
        target_user = User.query.get(receiver_id)
        if not target_user:
            print(f"Error: User {current_user.username} tried to send message to non-existent receiver {receiver_id}")
            return
        new_message.receiver_id = receiver_id
        room_id = str(min(user_id, receiver_id)) + '_' + str(max(user_id, receiver_id))
    elif group_id is not None: 
        target_group = Group.query.get(group_id)
        if not target_group or current_user not in target_group.members:
            print(f"Error: User {current_user.username} tried to send message to non-existent or inaccessible group {group_id}")
            return
        new_message.group_id = group_id
        # Group chat room ID
        room_id = 'group_' + str(group_id)
    else:
        print(f"Error: {current_user.username} sent a message without receiver_id or group_id.")
        return # No recipient specified

    db.session.add(new_message)
    db.session.commit()

    timestamp_utc = datetime.now(timezone.utc)

    # Prepare message data to send back to clients
    message_data = {
    'sender_id': new_message.sender_id,
    'sender_username': current_user.username,
    'content': new_message.content,
    'timestamp': timestamp_utc.isoformat(),  # <--- Send ISO string
    'receiver_id': new_message.receiver_id,
    'group_id': new_message.group_id
}
    socketio.emit('new_message', message_data, room=room_id)




