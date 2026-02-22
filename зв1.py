# grinmain.py
import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit, join_room, leave_room

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# HTML-шаблон (фронтенд) встроен прямо в код
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>GrinMain — аудиозвонок</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
        #status { margin: 20px; color: #333; }
        button { padding: 10px 20px; font-size: 16px; }
    </style>
    <script src="https://cdn.socket.io/4.5.0/socket.io.min.js"></script>
</head>
<body>
    <h1>GrinMain</h1>
    <p>Введите название комнаты (одинаковое для вас и друга)</p>
    <input type="text" id="roomInput" placeholder="комната">
    <button onclick="joinRoom()">Подключиться</button>
    <button onclick="hangUp()" disabled id="hangupBtn">Завершить</button>
    <div id="status"></div>

    <script>
        const socket = io();
        const roomInput = document.getElementById('roomInput');
        const statusDiv = document.getElementById('status');
        const hangupBtn = document.getElementById('hangupBtn');

        let localStream;
        let peerConnection;
        let room;
        let isInitiator = false;

        const config = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' }
            ]
        };

        async function getLocalStream() {
            try {
                localStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
                statusDiv.innerHTML = 'Микрофон получен';
                return true;
            } catch (e) {
                statusDiv.innerHTML = 'Ошибка доступа к микрофону: ' + e.message;
                return false;
            }
        }

        function createPeerConnection() {
            peerConnection = new RTCPeerConnection(config);
            localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));

            peerConnection.onicecandidate = event => {
                if (event.candidate) {
                    socket.emit('ice_candidate', {
                        room: room,
                        candidate: event.candidate
                    });
                }
            };

            peerConnection.ontrack = event => {
                const remoteAudio = document.createElement('audio');
                remoteAudio.srcObject = event.streams[0];
                remoteAudio.autoplay = true;
                remoteAudio.controls = false;
                document.body.appendChild(remoteAudio);
                statusDiv.innerHTML = 'Собеседник подключён';
            };

            peerConnection.onconnectionstatechange = () => {
                if (peerConnection.connectionState === 'disconnected') {
                    statusDiv.innerHTML = 'Соединение разорвано';
                    hangUp();
                }
            };
        }

        async function joinRoom() {
            room = roomInput.value.trim();
            if (!room) {
                alert('Введите название комнаты');
                return;
            }

            const streamOk = await getLocalStream();
            if (!streamOk) return;

            createPeerConnection();

            socket.emit('join', { room: room });
            statusDiv.innerHTML = 'Ожидание собеседника...';
            hangupBtn.disabled = false;
        }

        socket.on('user_joined', async () => {
            statusDiv.innerHTML = 'Собеседник появился, устанавливаем соединение...';
            isInitiator = true;

            const offer = await peerConnection.createOffer();
            await peerConnection.setLocalDescription(offer);
            socket.emit('offer', {
                room: room,
                sdp: peerConnection.localDescription
            });
        });

        socket.on('offer', async (data) => {
            statusDiv.innerHTML = 'Получен offer, отвечаем...';
            await peerConnection.setRemoteDescription(new RTCSessionDescription(data.sdp));
            const answer = await peerConnection.createAnswer();
            await peerConnection.setLocalDescription(answer);
            socket.emit('answer', {
                room: room,
                sdp: peerConnection.localDescription
            });
        });

        socket.on('answer', async (data) => {
            statusDiv.innerHTML = 'Получен answer';
            await peerConnection.setRemoteDescription(new RTCSessionDescription(data.sdp));
        });

        socket.on('ice_candidate', async (data) => {
            try {
                await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
            } catch (e) {
                console.error('Ошибка добавления ICE кандидата', e);
            }
        });

        socket.on('user_left', () => {
            statusDiv.innerHTML = 'Собеседник покинул комнату';
            hangUp();
        });

        function hangUp() {
            if (peerConnection) {
                peerConnection.close();
                peerConnection = null;
            }
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
                localStream = null;
            }
            if (room) {
                socket.emit('leave', { room: room });
                room = null;
            }
            statusDiv.innerHTML = 'Звонок завершён';
            hangupBtn.disabled = true;
            document.querySelectorAll('audio').forEach(el => el.remove());
        }
    </script>
</body>
</html>
"""

# Сигнальные обработчики Socket.IO
@socketio.on('join')
def on_join(data):
    room = data['room']
    join_room(room)
    emit('user_joined', {'user': 'peer'}, room=room, include_self=False)

@socketio.on('leave')
def on_leave(data):
    room = data['room']
    leave_room(room)
    emit('user_left', room=room, include_self=False)

@socketio.on('offer')
def on_offer(data):
    room = data['room']
    emit('offer', data, room=room, include_self=False)

@socketio.on('answer')
def on_answer(data):
    room = data['room']
    emit('answer', data, room=room, include_self=False)

@socketio.on('ice_candidate')
def on_ice_candidate(data):
    room = data['room']
    emit('ice_candidate', data, room=room, include_self=False)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=8080)