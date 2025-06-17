from flask import Blueprint, render_template,request, jsonify,current_app
from flask_login import login_required,current_user,login_user
from . import db
from .models import Message, User,UpdateProfileForm
from .utilis import save_profile_pic
from flask import render_template, redirect, url_for, flash, request
from datetime import datetime, timezone
import os 
from .models import User, Group
from .forms import CreateGroupForm
from werkzeug.utils import secure_filename
from dateutil import tz

views = Blueprint('views', __name__)


LOCAL_TZ = tz.gettz('Africa/Lagos')
if not LOCAL_TZ:
    print("Warning: 'Africa/Lagos' timezone not found. Using system local time as fallback.")
    LOCAL_TZ = tz.tzlocal()


@views.route('/home')
def home():
    return render_template('home.html')

# NEW default /chat route
@views.route('/chat')
@login_required
def chat_default():
    users = User.query.filter(User.id != current_user.id).all()
    if users:
        # Redirect to the first user's chat by default
        return redirect(url_for('views.chat_specific', chat_type='user', chat_id=users[0].id))
    else:
        # If no other users, display a default chat view (e.g., an empty one or a message)
        flash("No other users available to chat with yet. You can create a group!", "info")
        # Ensure that chat.html can render without chat_id or chat_type if this path is taken
        return render_template('chat.html', users=[], groups=current_user.groups, current_user=current_user, chat_title="No Chat Selected", profile_pic='avatar.jpg', chat_type=None, chat_id=None, cache_buster=datetime.now(timezone.utc).timestamp())


# Specific chat route (user or group)
@views.route('/chat/<chat_type>/<int:chat_id>')
@login_required
def chat_specific(chat_type, chat_id):
    users = User.query.filter(User.id != current_user.id).all()
    groups = current_user.groups
    
    chat_title = ""
    profile_pic_filename = 'avatar.jpg'
    
    # Initialize messages and other variables that need to be passed to template
    messages = []
    current_chat_id = chat_id
    current_chat_type = chat_type

    if chat_type == 'user':
        chat_partner = User.query.get(chat_id)
        if chat_partner:
            chat_title = chat_partner.username
            profile_pic_filename = chat_partner.profile_pic if chat_partner.profile_pic else 'avatar.jpg'
            # Load initial private messages
            messages_db = Message.query.filter(
                ((Message.sender_id == current_user.id) & (Message.receiver_id == chat_id)) |
                ((Message.sender_id == chat_id) & (Message.receiver_id == current_user.id))
            ).order_by(Message.timestamp).all()
            for msg in messages_db:
                dt_utc = msg.timestamp if msg.timestamp.tzinfo else msg.timestamp.replace(tzinfo=timezone.utc)
                local_timestamp = dt_utc.astimezone(LOCAL_TZ)
                messages.append({
                    'sender': msg.sender.username,
                    'content': msg.content,
                    'timestamp': local_timestamp.strftime("%H:%M"),
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
            # Load initial group messages
            messages_db = Message.query.filter_by(group_id=group.id).order_by(Message.timestamp).all()
            for msg in messages_db:
                dt_utc = msg.timestamp if msg.timestamp.tzinfo else msg.timestamp.replace(tzinfo=timezone.utc)
                local_timestamp = dt_utc.astimezone(LOCAL_TZ)
                messages.append({
                    'sender': msg.sender.username,
                    'content': msg.content,
                    'timestamp': local_timestamp.strftime("%H:%M"),
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
                            users=users,
                            groups=groups,
                            chat_title=chat_title,
                            profile_pic=profile_pic_filename, # Pass the filename
                            chat_type=current_chat_type, 
                            chat_id=current_chat_id,
                            initial_messages=messages, # Pass initial messages for display
                            current_user=current_user,
                            cache_buster=cache_buster)


@views.route('/send_message', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    content = data.get('content')
    group_id = data.get('group_id')
    receiver_id = data.get('receiver_id')

    if not content:
        return jsonify({'error': 'Empty message'}), 400

    if not group_id and not receiver_id:
        return jsonify({'error': 'No recipient specified'}), 400

    message = Message(
        content=content,
        sender_id=current_user.id,
        group_id=group_id,
        receiver_id=receiver_id,
        timestamp=datetime.now(timezone.utc) 
    )

    db.session.add(message)
    db.session.commit()

    return jsonify({'message': 'Message sent successfully'})


@views.route('/get_messages', methods=['GET'])
@login_required
def get_messages():
    group_id = request.args.get('group_id')
    receiver_id_str = request.args.get('receiver_id')

    messages_db = [] 
    if group_id:
        messages_db = Message.query.filter_by(group_id=group_id).order_by(Message.timestamp).all()
    elif receiver_id_str:
        try:
            receiver_id = int(receiver_id_str)
        except ValueError:
            return jsonify({'error': 'Invalid receiver_id'}), 400

        messages_db = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == receiver_id)) |
            ((Message.sender_id == receiver_id) & (Message.receiver_id == current_user.id))
        ).order_by(Message.timestamp).all()

    formatted = []
    for msg in messages_db: # Loop through messages_db
        dt_utc = msg.timestamp if msg.timestamp.tzinfo else msg.timestamp.replace(tzinfo=timezone.utc)
        local_timestamp = dt_utc.astimezone(LOCAL_TZ)

        formatted.append({
            'sender': msg.sender.username,
            'content': msg.content,
            'timestamp': local_timestamp.strftime("%H:%M"),
            'is_current_user_sender': msg.sender_id == current_user.id
        })

    return jsonify({'messages': formatted})


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


@views.route('/get_group_messages/<int:group_id>')
@login_required
def get_group_messages(group_id):
    messages_db = Message.query.filter_by(group_id=group_id).order_by(Message.timestamp.asc()).all()
    result = []
    for msg in messages_db:
        dt_utc = msg.timestamp if msg.timestamp.tzinfo else msg.timestamp.replace(tzinfo=timezone.utc)
        local_timestamp = dt_utc.astimezone(LOCAL_TZ)

        result.append({
            'sender': msg.sender.username,
            'content': msg.content,
            'timestamp': local_timestamp.strftime('%H:%M'),
            'is_current_user_sender': msg.sender_id == current_user.id 
        })
    return jsonify({'messages': result})


@views.route('/send_group_message/<int:group_id>', methods=['POST'])
@login_required
def send_group_message(group_id):
    data = request.get_json()
    content = data.get('content')

    if not content:
        return jsonify({'error': 'Empty message'}), 400

    msg = Message(
        content=content,
        sender_id=current_user.id,
        group_id=group_id,
        timestamp=datetime.now(timezone.utc) 
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({'status': 'sent'})


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