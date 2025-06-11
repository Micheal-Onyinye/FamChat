from flask import Blueprint, render_template,request, jsonify
from flask_login import login_required,current_user,login_user
from . import db
from .models import Message, User,UpdateProfileForm
from .utilis import save_profile_pic
from flask import render_template, redirect, url_for, flash, request
from datetime import datetime, timezone
import os 
from .models import User, Group
from .forms import CreateGroupForm

views = Blueprint('views', __name__)


@views.route('/home')
def home():
    return render_template('home.html')

@views.route('/chat')
@login_required
def chat():
    users = User.query.filter(User.id != current_user.id).all()
    groups = current_user.groups  # Only show groups user is part of
    cache_buster = datetime.now(timezone.utc).timestamp()
    return render_template('chat.html', users=users, groups=groups, current_user=current_user, cache_buster=cache_buster)

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
        receiver_id=receiver_id
    )

    db.session.add(message)
    db.session.commit()

    return jsonify({'message': 'Message sent successfully'})

@views.route('/get_messages', methods=['GET'])
@login_required
def get_messages():
    group_id = request.args.get('group_id')
    receiver_id_str = request.args.get('receiver_id')

    messages = []
    if group_id:
        messages = Message.query.filter_by(group_id=group_id).order_by(Message.timestamp).all()
    elif receiver_id_str:
        try:
            receiver_id = int(receiver_id_str)
        except ValueError:
            return jsonify({'error': 'Invalid receiver_id'}), 400

        messages = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.receiver_id == receiver_id)) |
            ((Message.sender_id == receiver_id) & (Message.receiver_id == current_user.id))
        ).order_by(Message.timestamp).all()

    formatted = [{
        'sender': msg.sender.username,
        'content': msg.content,
        'timestamp': msg.timestamp.strftime("%H:%M"),
        'is_current_user_sender': msg.sender_id == current_user.id
    } for msg in messages]

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
                return redirect(url_for('views.chat'))

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
    messages = Message.query.filter_by(group_id=group_id).order_by(Message.timestamp.asc()).all()
    result = [{
        'sender': msg.sender.username,
        'content': msg.content,
        'timestamp': msg.timestamp.strftime('%H:%M')
    } for msg in messages]
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
        group_id=group_id
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify({'status': 'sent'})

@views.route('/create-group', methods=['GET', 'POST'])
@login_required
def create_group():
    form = CreateGroupForm()
    form.members.choices = [(user.id, user.username) for user in User.query.filter(User.id != current_user.id).all()]

    if form.validate_on_submit():
        group = Group(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(group)
        group.members.append(current_user)

        for user_id in form.members.data:
            user = User.query.get(user_id)
            if user:
                group.members.append(user)

        db.session.commit()
        flash('Group created successfully!', 'success')
        return redirect(url_for('views.chat'))

    return render_template('create_group.html', form=form)
