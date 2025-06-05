from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField
from flask_wtf.file import FileAllowed
from wtforms.validators import DataRequired

# Association Table for User-Group many-to-many relationship
group_members = db.Table('group_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
)

# User Model
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    profile_pic = db.Column(db.String(150), nullable=False, default='avatar.jpg')
    last_seen = db.Column(db.DateTime(timezone=True), default=func.now())
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    confirmed = db.Column(db.Boolean, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)

    # Relationships
    messages = db.relationship('Message', foreign_keys='Message.sender_id', backref='sender', lazy=True)
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_id', backref='receiver', lazy=True)
    call_histories = db.relationship('CallHistory', backref='caller', lazy=True)
    notifications = db.relationship('Notification', backref='recipient', lazy=True)
    message_statuses = db.relationship('MessageStatus', backref='user', lazy=True)
    groups = db.relationship('Group', secondary=group_members, backref=db.backref('members', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'


# Message Model
class Message(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(10000), nullable=True)
    timestamp = db.Column(db.DateTime(timezone=True), default=func.now())
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=True)

    status = db.relationship('MessageStatus', backref='message', lazy=True)

    def __repr__(self):
        return f'<Message {self.id}>'


# Group Model
class Group(db.Model):
    __tablename__ = 'group'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())

    messages = db.relationship('Message', backref='group', lazy=True, overlaps="members,groups")

    def __repr__(self):
        return f'<Group {self.name}>'


# Media Model
class Media(db.Model):
    __tablename__ = 'media'
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(300), nullable=False)
    file_type = db.Column(db.String(50), nullable=True)
    uploaded_at = db.Column(db.DateTime(timezone=True), default=func.now())

    messages = db.relationship('Message', backref='media', lazy=True)

    def __repr__(self):
        return f'<Media {self.id}>'


# Message Status Model
class MessageStatus(db.Model):
    __tablename__ = 'message_status'
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), default='sent')  # sent, delivered, read

    def __repr__(self):
        return f'<MessageStatus {self.status}>'


# Notification Model
class Notification(db.Model):
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.String(300), nullable=False)
    seen = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())

    def __repr__(self):
        return f'<Notification {self.id}>'


# Call History Model
class CallHistory(db.Model):
    __tablename__ = 'call_history'
    id = db.Column(db.Integer, primary_key=True)
    caller_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    call_type = db.Column(db.String(50), nullable=False)  # voice or video
    duration = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime(timezone=True), default=func.now())

    def __repr__(self):
        return f'<CallHistory {self.id} - {self.call_type}>'


# Form for Updating User Profile
class UpdateProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    profile_pic = FileField('Upload Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Update Profile')


print("✅ models.py loaded correctly")
print(User.__table__)
