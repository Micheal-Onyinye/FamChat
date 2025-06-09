from flask import Blueprint, render_template,request, jsonify
from flask_login import login_required,current_user,login_user
from . import db
from .models import Message, User,UpdateProfileForm
from .utilis import save_profile_pic
from flask import render_template, redirect, url_for, flash, request
from datetime import datetime, timezone
import os 



views = Blueprint('views', __name__)
@views.route ('/home')
def home():
    return render_template('home.html')

@views.route('/chat')
@login_required
def chat():
    #To Get all users except the current user
    users = User.query.filter(User.id != current_user.id).all()
    cache_buster = datetime.now(timezone.utc).timestamp()
    return render_template('chat.html', users=users, current_user=current_user, cache_buster=cache_buster)

@views.route('/send_message', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    content = data.get('content')
    group_id = data.get('group_id')     
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
    receiver_id_str = request.args.get('receiver_id')

    # ... (your existing print statements for debugging) ...

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
        # --- ADD THIS LINE ---
        'is_current_user_sender': msg.sender_id == current_user.id 
        # --- END ADDITION ---
    } for msg in messages]

    return jsonify({'messages': formatted})

@views.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        print(f"--- Profile Update Attempt ---")
        print(f"Original username: {current_user.username}")
        print(f"Original profile_pic in DB (before update): {current_user.profile_pic}")

        if form.profile_pic.data:
            print(f"Profile picture data received from form.")
            try:
                pic_file = save_profile_pic(form.profile_pic.data)
                current_user.profile_pic = pic_file
                print(f"save_profile_pic returned: {pic_file}")
            except Exception as e:
                print(f"Error saving profile picture: {e}")
                flash(f"Error uploading profile picture: {e}", 'danger')
                return redirect(url_for('views.chat'))
        else:
            print("No new profile picture data in form.")

        #To Update username
        current_user.username = form.username.data
        print(f"New username set to: {current_user.username}")

        db.session.commit()
        print(f"DB committed. Current_user.profile_pic AFTER commit: {current_user.profile_pic}")

        flash('Your profile has been updated!', 'success')

        #To Verify the actual file exists on the filesystem
        if current_user.profile_pic:
            upload_folder = os.path.join(os.getcwd(), 'static', 'profile_pic')
            file_path = os.path.join(upload_folder, current_user.profile_pic)
            if os.path.exists(file_path):
                print(f"CONFIRM: File '{file_path}' exists on filesystem.")
            else:
                print(f"WARNING: File '{file_path}' DOES NOT exist on filesystem!")
        else:
            print("No profile_pic set for current_user, so no file to check.")

        print(f"Redirecting to: {url_for('views.profile')}")
        return redirect(url_for('views.profile'))
    else:
        
        if request.method == 'POST':
            print(f"Form validation failed. Errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"Error in {field}: {error}", 'danger')

    form.username.data = current_user.username
    cache_buster = datetime.now(timezone.utc).timestamp()
    print(f"Rendering profile.html. Current_user.profile_pic: {current_user.profile_pic}")
    print(f"Cache buster: {cache_buster}")
    return render_template('profile.html', form=form, cache_buster=cache_buster)