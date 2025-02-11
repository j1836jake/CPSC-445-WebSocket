from flask import Flask, request
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store connected users
active_users = {}

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
    print("Client disconnected!")  # This prints on disconnect

@socketio.on('register')
def handle_registration(data):
    username = data.get('username')

    # Checks if username is valid and available
    if username is None or username == "":
        emit('registration_response', {'success': False, 'message': 'Invalid username'})
    elif username in active_users:
        emit('registration_response', {'success': False, 'message': 'Username already taken'})
    else:
        # Store user info
        active_users[username] = {'sid': request.sid}
        # Notification of successful registration
        emit('registration_response', {'success': True, 'message': f'Welcome {username}!'})
        # Notify other users about new user
        #emit('user_joined', {'username': username}, broadcast=True, include_self=False)


@socketio.on('private_message')
def handle_private_message(data):
    recipient_name = data.get('recipient')
    message = data.get('message')

    # Find sender's username from their sid
    sender_name = None
    for username, user_data in active_users.items():
        if user_data['sid'] == request.sid:
            sender_name = username
            break

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
    socketio.run(app, debug=True, host='0.0.0.0', port=5001)