from asyncio import timeout

import socketio
import sys
import getpass
import time

SERVER_URL = "http://localhost:5001"
EXIT_COMMAND = "exit"

registration_response = None  # Stores server response
user_check_response = None  # Stores server response
login_response = None  # Stores login response from the server

print("Starting client...")  # Added print

# Create Socket.IO client
sio = socketio.Client(ssl_verify= False,
                      reconnection= True,
                      reconnection_attempts = 5, # max reconnection attempts
                      reconnection_delay = 1, # delay w/ 1 sec
                      reconnection_delay_max = 5, # max 5 sec between attempts
)

@sio.event
def connect():
    print("Connected to server!")
    print("Connection established, waiting for registration...")

    while True:
        choice = input("Do you want to (L)ogin or (R)egister? ").strip().lower()

        if choice == 'r':
            register()
            break
        elif choice == 'l':
            login()
            break
        else:
            print("Invalid choice. Please enter 'L' to login or 'R' to register.")

@sio.event()
def connect_error(data):
        print("\n!!! Connection Error. Attempting to reconnect...\n")


def register():
    while True:
        username = input("Enter your username: ").strip()
        password = getpass.getpass("Enter your password: ").strip()

        sio.emit('register', {'username': username, 'password': password})
        response = wait_for_registration_response()

        if response['success']:
            print(f"Registration successful: {response['message']}")
            start_chat()
            break
        else:
            print(f"Registration failed: {response['message']}. Try again.")

def login():
    while True:
        username = input("Enter your username: ").strip()
        password = getpass.getpass("Enter your password: ").strip()

        sio.emit('login', {'username': username, 'password': password})
        response = wait_for_login_response()

        if response['success']:
            print(f"Login successful: {response['message']}")
            sio.emit('mark_online', {'username': username})  # Ensure server marks user as online
            start_chat()
            break
        else:
            print(f"Login failed: {response['message']}. Try again.")

def wait_for_login_response():
    """Waits for the login response from the server before proceeding."""
    global login_response
    login_response = None  # Reset response

    start_time = time.time()
    while login_response is None:
        if time.time() - start_time > 5:  # Timeout after 5 seconds
            return {'success': False, 'message': 'Server timeout'}
    return login_response

@sio.on('login_response')
def handle_login_response(data):
    global login_response
    login_response = data  # Store the response for waiting function


def wait_for_registration_response():
    """Waits for the registration response from the server before proceeding."""
    global registration_response
    registration_response = None  # Reset response

    # Wait until response is received
    start_time = time.time()
    while registration_response is None:
        if time.time() - start_time > 5:  # Timeout after 5 seconds
            return {'success': False, 'message': 'Server timeout'}
    return registration_response

@sio.on('registration_response')
def handle_registration_response(data):
    global registration_response
    registration_response = data  # Store the response for the waiting loop

@sio.on('user_joined')
def handle_user_joined(data):
    print(f"\n*** User {data['username']} has joined the chat!\n")

@sio.on('user_check_response')
def handle_user_check_response(data):
    global user_check_response
    user_check_response = data  # Store response for waiting function

@sio.on('new_private_message')
def handle_private_message(data):
        print(f"\n{data['sender']}: {data['message']}\nYou: ", end='', flush=True)


@sio.on('message_error')
def handle_message_error(data):
    print(f"Error: {data['message']}")

def wait_for_user_check_response():
    """Waits for the user check response before proceeding."""
    global user_check_response
    user_check_response = None  # Reset response
    timeout = 5

    start_time = time.time()
    while user_check_response is None:
        if time.time() - start_time > timeout:
            return {'exists': False}  # Timeout response
    return user_check_response


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

def disconnect_client():
    print("Disconnecting from server...")
    sio.disconnect()
    sys.exit(0)

def main():
    try:
        print("Attempting to connect to server...")
        sio.connect(SERVER_URL)  # Connect to server
        sio.wait()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        sio.disconnect()

if __name__ == '__main__':
    main()
