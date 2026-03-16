# FamChat
## Overview
**FamChat** is a real-time web chat application built with Flask, Flask-SocketIO, and SQLAlchemy. Users can register, login, create and join groups, send private messages, and chat in real-time with other users. The platform supports emojis, media attachments, and maintains chat history.

# Features

- **User authentication**: Sign up, login, logout, reset password.

- **Real-time chat with private and group messaging using Socket.IO.**

- **Emoji support via EmojiButton.**

- **User profile pictures and group avatars.**

- **Responsive UI for mobile and desktop.**

- **Persistent message history stored in a database.**

- **Active chat highlighting in the sidebar.**

- **Basic notification system for new messages.**

# Tech Stack

- **Backend**: Python, Flask, Flask-SocketIO, Flask-Login, Flask-WTF, SQLAlchemy

- **Frontend**: HTML, CSS, JavaScript, Bootstrap, EmojiButton

- **Database**: SQLite (default)

## Other Libraries: PIL (for image processing), python-dotenv

# Installation

**Clone the repository**

git clone https://github.com/Micheal-Onyinye/FamChat.git
cd FamChat

Create a virtual environment

python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

**Install dependencies**

pip install -r requirements.txt

Set environment variables

Create a .env file in the root:

SECRET_KEY=your_secret_key

Initialize the database

from APP import create_database, define_app
app = define_app()
create_database(app)

Run the app

flask run
# Or if using SocketIO for live chat:
python run.py
Usage

Register a new user via /sign_up.

Login via /login.

Join the "General Chat" group automatically created for all users.

Send private messages or create/join groups.

Messages appear in real-time and are stored in the database.

Use the emoji picker to add emojis to messages.

# Folder Structure
```test
FamChat/
│
├── APP/
│   ├── __init__.py          # App factory and database setup
│   ├── models.py            # Database models
│   ├── views.py             # Flask routes
│   ├── auth.py              # Authentication routes
│   ├── forms.py             # Flask-WTF forms
│   ├── utilis.py            # Utility functions (e.g., save profile pics)
│   └── static/              # CSS, JS, images
│       ├── profile_pic/     
│       ├── bg2.jpg
│       └── images/
│
├── templates/               # HTML templates
│   ├── chat.html
│   ├── login.html
│   ├── sign_up.html
│   └── reset_password.html
│
├── .env                     # Environment variables
├── database.db              # SQLite database
├── requirements.txt         # Python dependencies
└── app.py                   # Entry point (if using SocketIO)
