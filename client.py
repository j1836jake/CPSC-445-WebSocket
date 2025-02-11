import socketio
import sys
import re
import threading

SERVER_URL = "http://localhost:5001"
EXIT_COMMAND = "exit"
registration_response = None  # Stores server response
user_check_response = None  # Stores server response

print("Starting client...")  # Added print

# Create Socket.IO client
sio = socketio.Client()

@sio.event
def connect():
    print("Connected to server!")
    print("Connection established, waiting for registration...")

    while True:
        username = input("Enter your username: ").strip()
        # Send registration request
        sio.emit('register', {'username': username})

        # Wait for response before continuing
        response = wait_for_registration_response()

        if response['success']:
            print(f"Registration successful: {response['message']}")
            start_chat()
            break  # Exit loop and start chat after success
        else:
            print(f"Registration failed: {response['message']}. Try again.")


def wait_for_registration_response():
    """Waits for the registration response from the server before proceeding."""
    global registration_response
    registration_response = None  # Reset response

    # Wait until response is received
    while registration_response is None:
        pass  # Keep looping until response arrives

    return registration_response


@sio.on('registration_response')
def handle_registration_response(data):
    global registration_response
    registration_response = data  # Store the response for the waiting loop

@sio.on('user_joined')
def handle_user_joined(data):
    print(f"\n*** User {data['username']} has joined the chat!\n")

@sio.event
def disconnect():
    print("Disconnected from server!")
    reconnect()

def disconnect_client():
    print("Disconnecting from server...")
    sio.disconnect()
    sys.exit(0)

def reconnect():
    print("Attempting to reconnect...")
    try:
        sio.connect(SERVER_URL)
        print("Reconnected successfully!")
    except Exception as e:
        print(f"Reconnection failed: {e}")

@sio.on('user_left')
def handle_user_left(data):
    print(f"\n--- User {data['username']} has left the chat!\n")


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
    print(f"\n{data['sender']}: {data['message']}\nYou: ", end='', flush=True)

# @sio.on('message_sent')
# def handle_message_sent(data):
#     print("Message sent!\nYou: ", end='', flush=True)

@sio.on('message_error')
def handle_message_error(data):
    print(f"Error: {data['message']}")

def wait_for_user_check_response():
    """Waits for the user check response before proceeding."""
    global user_check_response
    user_check_response = None  # Reset response

    while user_check_response is None:
        pass  # Keep looping until response arrives

    return user_check_response

@sio.on('user_check_response')
def handle_user_check_response(data):
    global user_check_response
    user_check_response = data  # Store response for waiting function


def start_chat():
    print(f"\nType '{EXIT_COMMAND}' at any time to disconnect.")

    while True:
        recipient = input("\nEnter username to chat with: ")
        if recipient.lower() == EXIT_COMMAND:
            disconnect_client()

        # Check if recipient exists before starting chat
        sio.emit('check_user', {'username': recipient})
        response = wait_for_user_check_response()

        if not response['exists']:
            print(f"\n!!!! User '{recipient}' is not online. Try another user.\n")
            continue  # Loop again for a valid username


        print(f"\nStarting chat with {recipient}. Type 'exit' to switch users.\n")

        while True:
            message = input("You: ")
            if message.lower() == 'exit':
                break
            elif message.lower() == EXIT_COMMAND:
                disconnect_client()

            sio.emit('private_message', {
                'recipient': recipient,
                'message': message
            })

def main():
    try:
        print("Attempting to connect to server...")  # Added print
        sio.connect('http://localhost:5001') # Connect to server and keep connection open

        sio.wait()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sio.disconnect()

if __name__ == '__main__':
    main()
