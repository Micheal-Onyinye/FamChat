from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func

# Association Table for User-Group many-to-many relationship
group_members = db.Table('group_members',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('group_id', db.Integer, db.ForeignKey('group.id'), primary_key=True)
)

# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    profile_picture = db.Column(db.String(150), nullable=True)
    last_seen = db.Column(db.DateTime(timezone=True), default=func.now())
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())
    confirmed = db.Column(db.Boolean, default=False)
    confirmed_on = db.Column(db.DateTime, nullable=True)

    # Relationships
    messages = db.relationship('Message', backref='sender', lazy=True)
    call_histories = db.relationship('CallHistory', backref='caller', lazy=True)
    notifications = db.relationship('Notification', backref='recipient', lazy=True)
    groups = db.relationship('Group', secondary=group_members, backref='members', lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

# Message Model
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(10000))
    timestamp = db.Column(db.DateTime(timezone=True), default=func.now())
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=True)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=True)

    # Message Status Relationship
    status = db.relationship('MessageStatus', backref='message', lazy=True)

    def __repr__(self):
        return f'<Message {self.id}>'

# Group Model
class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.String(300))
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())

    # Members are now accessed via the secondary table
    # members = db.relationship('User', secondary=group_members, backref='groups', lazy='dynamic') # Defined in User

    
    messages = db.relationship('Message', backref='group', lazy=True, overlaps="members,groups")

    def __repr__(self):
        return f'<Group {self.name}>'


# Media Model
class Media(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_path = db.Column(db.String(300), nullable=False)
    file_type = db.Column(db.String(50))
    uploaded_at = db.Column(db.DateTime(timezone=True), default=func.now())

    def __repr__(self):
        return f'<Media {self.id}>'

# Message Status Model
class MessageStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, db.ForeignKey('message.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(50), default='sent')  # sent, delivered, read

    def __repr__(self):
        return f'<MessageStatus {self.status}>'

# Notification Model
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.String(300))
    seen = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=func.now())

    def __repr__(self):
        return f'<Notification {self.id}>'

# Call History Model
class CallHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    caller_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    call_type = db.Column(db.String(50))  # voice or video
    duration = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime(timezone=True), default=func.now())

    def __repr__(self):
        return f'<CallHistory {self.id} - {self.call_type}>'

print("✅ models.py loaded correctly")
print(User.__table__)