import socketio

# Create a WebSocket client
sio = socketio.Client()

# Connect to the Flask-SocketIO server
sio.connect("http://127.0.0.1:5000")

# Send a test message
sio.send("Hello WebSocket! Unique message")

# Define how to handle incoming messages
@sio.on("message")
def on_message(data):
    print(f"Received from server: {data}")

# Keep connection alive for a few seconds
sio.wait()
