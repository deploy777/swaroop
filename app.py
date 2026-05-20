
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from datetime import datetime
import base64
import os
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kiet-chat-secret-2026'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

socketio = SocketIO(app, cors_allowed_origins="*", max_http_buffer_size=50*1024*1024)

online_users = {}
chat_history = []

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print(f"[+] Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    sid = request.sid
    if sid in online_users:
        username = online_users[sid]
        del online_users[sid]
        emit('user_left', {
            'username': username,
            'online_users': list(online_users.values()),
            'count': len(online_users)
        }, broadcast=True)
        print(f"[-] {username} disconnected")

@socketio.on('join')
def handle_join(data):
    username = data.get('username', 'Anonymous')
    online_users[request.sid] = username
    emit('user_joined', {
        'username': username,
        'online_users': list(online_users.values()),
        'count': len(online_users)
    }, broadcast=True)

    for msg in chat_history[-50:]:
        emit('message', msg)

    print(f"[+] {username} joined the chat")

@socketio.on('send_message')
def handle_message(data):
    username = online_users.get(request.sid, 'Anonymous')
    msg_data = {
        'id': str(uuid.uuid4())[:8],
        'username': username,
        'message': data.get('message', ''),
        'timestamp': datetime.now().strftime("%I:%M %p"),
        'type': 'text'
    }
    chat_history.append(msg_data)
    if len(chat_history) > 200:
        chat_history.pop(0)
    emit('message', msg_data, broadcast=True)

@socketio.on('send_file')
def handle_file(data):
    username = online_users.get(request.sid, 'Anonymous')
    filename = data.get('filename', 'file')
    file_data = data.get('data', '')
    file_size = data.get('size', 0)

    safe_name = f"{uuid.uuid4().hex[:8]}_{filename}"
    file_path = os.path.join(UPLOAD_FOLDER, safe_name)

    try:
        raw = base64.b64decode(file_data)
        with open(file_path, 'wb') as f:
            f.write(raw)
    except Exception as e:
        emit('error', {'message': f'File save failed: {str(e)}'})
        return

    msg_data = {
        'id': str(uuid.uuid4())[:8],
        'username': username,
        'filename': filename,
        'saved_as': safe_name,
        'size': file_size,
        'timestamp': datetime.now().strftime("%I:%M %p"),
        'type': 'file'
    }
    chat_history.append(msg_data)
    emit('message', msg_data, broadcast=True)

@socketio.on('send_image')
def handle_image(data):
    username = online_users.get(request.sid, 'Anonymous')
    filename = data.get('filename', 'image.png')
    img_data = data.get('data', '')

    safe_name = f"{uuid.uuid4().hex[:8]}_{filename}"
    file_path = os.path.join(UPLOAD_FOLDER, safe_name)

    try:
        raw = base64.b64decode(img_data)
        with open(file_path, 'wb') as f:
            f.write(raw)
    except Exception as e:
        emit('error', {'message': f'Image save failed: {str(e)}'})
        return

    msg_data = {
        'id': str(uuid.uuid4())[:8],
        'username': username,
        'filename': filename,
        'saved_as': safe_name,
        'image_data': img_data,
        'timestamp': datetime.now().strftime("%I:%M %p"),
        'type': 'image'
    }
    chat_history.append(msg_data)
    emit('message', msg_data, broadcast=True)

@socketio.on('typing')
def handle_typing(data):
    username = online_users.get(request.sid, 'Anonymous')
    emit('user_typing', {'username': username}, broadcast=True, include_self=False)

@socketio.on('stop_typing')
def handle_stop_typing(data):
    username = online_users.get(request.sid, 'Anonymous')
    emit('user_stop_typing', {'username': username}, broadcast=True, include_self=False)

if __name__ == '__main__':
    print("\n  KIET Engineering College - Chat Server")
    print("  Running on http://127.0.0.1:5050\n")
    socketio.run(app, host='127.0.0.1', port=5050, debug=True, allow_unsafe_werkzeug=True)
