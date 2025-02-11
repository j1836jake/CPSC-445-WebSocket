import socketio
import sys

print("Starting client...")  # Added print

# Create Socket.IO client
sio = socketio.Client()

@sio.event
def connect():
    print("Connected to server!")

    username = input("Enter your username: ")
    # Send registration request
    sio.emit('register', {'username': username})

@sio.on('registration_response')
def handle_registration_response(data):
    if data['success']:
        print(f"Registration successful: {data['message']}")
        while True:
            start_chat() # Allow sending messages after registration
    else:
        print(f"Registration failed: {data['message']}")

@sio.on('user_joined')
def handle_user_joined(data):
    print(f"User {data['username']} has joined the chat!")

@sio.event
def disconnect():
    print("Disconnected from server!")

@sio.on('server_response')
def on_message(data): # When server sends 'server_response'
    print(f"Received from server: {data}")

def send_message():
    recipient = input("Enter recipient's username: ")
    message = input("Enter your message: ")
    sio.emit('private_message', {
        'recipient': recipient,
        'message': message
    })

@sio.on('new_private_message')
def handle_private_message(data):
    print(f"\nMessage from {data['sender']}: {data['message']}")
    print("You: ", end='', flush=True)  # Return to input position

@sio.on('message_sent')
def handle_message_sent(data):
    print(f"Message sent to {data['recipient']}")

@sio.on('message_error')
def handle_message_error(data):
    print(f"Error: {data['message']}")

def start_chat():
    recipient = input("Enter username to chat with: ")
    print(f"Starting chat with {recipient}. Type 'exit' to choose a new recipient.")
    while True:
        message = input("You: ")
        if message.lower() == 'exit':
            break
        sio.emit('private_message', {
            'recipient': recipient,
            'message': message
        })

def main():
    try:
        print("Attempting to connect to server...")  # Added print
        sio.connect('http://localhost:5001') # Connect to server and keep connection open
        print("Connection established, waiting...")  # Added print
        sio.wait()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sio.disconnect()

if __name__ == '__main__':
    main()
