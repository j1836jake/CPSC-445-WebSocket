from flask import Flask, request
from flask_socketio import SocketIO, emit
import re
import hashlib
import time

app = Flask(__name__)
socketio = SocketIO(app,
                    cors_allowed_origins="*",
                    ping_timeout = 10, # secs waited for ping response
                    ping_interval = 5) # secs between pings

# Store connected users
active_users = {}

HOST = "0.0.0.0"
PORT = 5001

@app.route('/')
def index():
    print("Homepage accessed!")  # Added print
    return "SecureChat Server Running"

@socketio.on('connect')
def handle_connect():
    print("Client connected!")  # This should print when a client connects
    emit('server_response', {'data': 'Connected to server'})


@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected!")

    # Find the username associated with this session ID
    disconnected_user = None
    for username, user_data in list(active_users.items()):
        if user_data['sid'] == request.sid:
            disconnected_user = username
            del active_users[username]
            break

    # Broadcast user leaving (if they were registered)
    if disconnected_user:
        print(f"{disconnected_user} has left the chat.")
        emit('user_left', {'username': disconnected_user}, broadcast=True, include_self=False)

@socketio.on('check_user')
def handle_check_user(data):
    username = data.get('username')
    exists = username in active_users
    emit('user_check_response', {'exists': exists})

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

    # Check if username exists
    if username not in active_users:
        emit('login_response', {'success': False, 'message': 'Invalid username or password'})
        return

    # Verify password
    hashed_password = hash_password(password)
    if hashed_password != active_users[username]['password']:
        emit('login_response', {'success': False, 'message': 'Invalid username or password'})
        return

    # Allow login and send confirmation
    active_users[username]['sid'] = request.sid  # Update session ID
    emit('login_response', {'success': True, 'message': f'Welcome back, {username}!'})


@socketio.on('register')
def handle_registration(data):
    username = data.get('username')
    password = data.get('password')

    # Convert to lowercase for case-insensitive uniqueness
    username_lower = username.lower()

    # Checks if username is valid and available
    if not is_valid_username(username):
        emit('registration_response', {'success': False, 'message': 'Invalid username! Use only letters, numbers, and underscores.'})
        return
    if username_lower in (u.lower() for u in active_users):
        emit('registration_response', {'success': False, 'message': 'Username already taken'})
        return
    if len(password) < 6:
        emit('registration_response', {'success': False, 'message': 'Password must be at least 6 characters'})
        return
    else:
        # Hash the password before storing
        hashed_password = hash_password(password)

        # Store user info
        active_users[username] = {'sid': request.sid,
                                  'password': hashed_password,
                                  'message_timestamps': [] # tracks message times
        }

        # Notification of successful registration
        emit('registration_response', {'success': True, 'message': f'Welcome {username}!'})

        # Notify all other users that a new user has joined
        emit("user_joined", {"username": username}, broadcast=True, include_self=False)

@socketio.on('private_message')
def handle_private_message(data):
    current_time = time.time()
    recipient_name = data.get('recipient')
    message = data.get('message')

    # Find sender's username from their sid
    sender_name = None
    for username, user_data in active_users.items():
        if user_data['sid'] == request.sid:
            sender_name = username
            break
    # Future implement, token approach?
    if sender_name:
        # Get user's message time and removess old ones,more than 10 secs
        user_timestamps = active_users[sender_name]['message_timestamps']
        user_timestamps = [ts for ts in user_timestamps if current_time - ts < 10]
        active_users[sender_name]['message_timestamps'] = user_timestamps

        # Check if user has sent too many messages
        if len(user_timestamps) >= 5:
            emit('message_error', {
                'message': 'Rate limit exceeded. Please wait before sending more messages.'
            })
            return

        # Add current message timestamp
        user_timestamps.append(current_time)

        # Check if recipient exists
        if recipient_name in active_users:
            recipient_sid = active_users[recipient_name]['sid']
            # Emit message to only the recipient
            emit('new_private_message', {
                'sender': sender_name,
                'message': message
            }, room = recipient_sid)
            # Also send confirmation to sender
            emit('message_sent', {
                'recipient': recipient_name,
                'message': message
            })
        else:
            # If recipient doesn't exist, send error to sender
            emit('message_error', {
                'message': f'User {recipient_name} not found'
            })


if __name__ == '__main__':
    print("Starting server...")  # Added print
    socketio.run(app,
                     debug=True,
                     host=HOST,
                     port=PORT,
                     ssl_context=('cert.pem', 'key.pem'))