from flask import Flask
from flask_socketio import SocketIO

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/')
def index():
    return "WebSocket server is running!"

@socketio.on('message')
def handle_message(msg):
    print(f"Received message: {msg}")
    socketio.send(f"Echo: {msg}")

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
