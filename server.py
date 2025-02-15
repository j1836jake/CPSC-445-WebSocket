from flask import Flask, request
from flask_socketio import SocketIO, emit
import sqlite3
import re
import hashlib
import time

app = Flask(__name__)
socketio = SocketIO(app,
                    cors_allowed_origins="*",
                    ping_timeout = 10, # secs waited for ping response
                    ping_interval = 5) # secs between pings

# Store connected users
user_message_timestamps = {}

HOST = "0.0.0.0"
PORT = 5001

DB_FILE = "chat.db"

def init_db():
    """Ensures the database is initialized properly without overwriting existing tables."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Ensure WAL mode is enabled for persistence
    cursor.execute("PRAGMA journal_mode=WAL;")

    # Create tables ONLY IF they do not already exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        sid TEXT DEFAULT NULL
                     )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        sender TEXT NOT NULL,
                        recipient TEXT NOT NULL,
                        message TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                     )''')

    conn.commit()
    conn.close()

    print("Database initialized successfully (without overwriting existing tables).")


init_db()


def mark_user_online(username, sid):
    """Marks a user as online by storing their session ID in the database and committing the update."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print(f"Marking {username} online with SID {sid}")

    cursor.execute("UPDATE users SET sid = ? WHERE username = ?", (sid, username))

    if cursor.rowcount == 0:
        print(f"WARNING: User {username} not found in database, cannot mark online.")
    else:
        print(f"SUCCESS: User {username} is now ONLINE with SID: {sid}")

    conn.commit()  # Force commit to database
    conn.close()



def mark_user_offline(sid):
    """Marks a user as offline by removing their session ID."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET sid = NULL WHERE sid = ?", (sid,))
    conn.commit()
    conn.close()


def is_user_online(username):
    """Checks if a user is online by verifying their session ID in the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT sid FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    return row is not None and row[0] is not None


@socketio.on('connect')
def handle_connect():
    print("Client connected!")  # This should print when a client connects
    emit('server_response', {'data': 'Connected to server'})


@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected!")
    mark_user_offline(request.sid)

def is_valid_username(username):
    """Validate username: Only letters, numbers, and underscores, between 3-15 characters."""
    return bool(re.match(r'^[a-zA-Z0-9_]{3,15}$', username))  # Restrict length

def hash_password(password):
    """Hash a password for secure storage."""
    return hashlib.sha256(password.encode()).hexdigest()

@socketio.on('login')
def handle_login(data):
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()

        if row and row[0] == hash_password(password):
            print(f"User {username} logged in. Calling mark_user_online() with SID {request.sid}")
            mark_user_online(username, request.sid)
            emit('login_response', {'success': True, 'message': f'Welcome back, {username}!'})
        else:
            emit('login_response', {'success': False, 'message': 'Invalid username or password'})

    except Exception as e:
        print(f"Database error on login: {e}")
        emit('login_response', {'success': False, 'message': 'Server error'})

    finally:
        conn.close()


@socketio.on('register')
def handle_registration(data):
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    hashed_password = hash_password(password)

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()

        # Insert new user into the database
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()

        # Mark user as online immediately after registration
        sid = request.sid  # Get session ID
        cursor.execute("UPDATE users SET sid = ? WHERE username = ?", (sid, username))
        conn.commit()

        print(f"✅ SUCCESS: User {username} registered and marked online (SID: {sid})")

        # Notification of successful registration
        emit('registration_response', {'success': True, 'message': f'Welcome {username}!'})

    except sqlite3.IntegrityError:
        emit('registration_response', {'success': False, 'message': 'Username already taken'})

    except Exception as e:
        print(f"Database error on registration: {e}")
        emit('registration_response', {'success': False, 'message': 'Server error'})

    finally:
        conn.close()


@socketio.on('check_user')
def handle_check_user(data):
    username = data.get('username')
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT sid FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()

    exists = row is not None and row[0] is not None  # Ensure SID is not NULL

    print(f"Checking user {username}: {'ONLINE' if exists else 'OFFLINE'}")  # Debugging log

    emit('user_check_response', {'exists': exists})


@socketio.on('private_message')
def handle_private_message(data):
    global user_message_timestamps  # Ensure global reference

    current_time = time.time()
    recipient_name = data.get('recipient')
    message = data.get('message')

    # Find sender's username from their sid
    sender_name = None
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Get sender's username from their session ID
    cursor.execute("SELECT username FROM users WHERE sid = ?", (request.sid,))
    row = cursor.fetchone()
    if row:
        sender_name = row[0]

    if not sender_name:
        emit('message_error', {'message': 'Invalid sender. Please re-login.'})
        return

    # Initialize rate limit tracking for user if not already set
    if sender_name not in user_message_timestamps:
        user_message_timestamps[sender_name] = []

    # Remove timestamps older than 10 seconds
    user_message_timestamps[sender_name] = [ts for ts in user_message_timestamps[sender_name] if current_time - ts < 10]

    # Check if user has exceeded the message limit
    if len(user_message_timestamps[sender_name]) >= 5:
        emit('message_error', {'message': 'ERROR: Rate limit exceeded. Please wait before sending more messages.'})
        return

    # Add the current message timestamp
    user_message_timestamps[sender_name].append(current_time)

    if sender_name and recipient_name:
        # Store the message in the database
        cursor.execute("INSERT INTO messages (sender, recipient, message) VALUES (?, ?, ?)",
                       (sender_name, recipient_name, message))
        conn.commit()

        # Get recipient's session ID
        cursor.execute("SELECT sid FROM users WHERE username = ? AND sid IS NOT NULL AND sid != ''", (recipient_name,))
        recipient_row = cursor.fetchone()
        conn.close()

        if not recipient_row or not recipient_row[0]:  # Ensure recipient is online
            emit('message_error', {'message': f'ERROR: User {recipient_name} is offline. Message not sent.'})
            return

        recipient_sid = recipient_row[0]
        print(f" Sending message from {sender_name} to {recipient_name} (SID: {recipient_sid})")

        # Emit message to recipient
        emit('new_private_message', {'sender': sender_name, 'message': message}, room=recipient_sid)

        # Confirm message sent to sender
        emit('message_sent', {'recipient': recipient_name, 'message': message})
    else:
        emit('message_error', {'message': f'User {recipient_name} is not online or does not exist'})

if __name__ == '__main__':
    print("Starting server with SQLite support...")
    socketio.run(app, debug=True, host=HOST, port=PORT)
