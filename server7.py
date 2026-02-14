import asyncio
import json
from aiohttp import web

# ========== CloudPub SDK ==========
CLOUDPUB_AVAILABLE = False
cloudpub_info = None

try:
    from cloudpub_python_sdk import Connection, Protocol, Auth
    CLOUDPUB_AVAILABLE = True
except ImportError:
    print("⚠️ CloudPub не установлен. Установите: pip install cloudpub-python-sdk")

# ========== ВАШИ ДАННЫЕ CLOUDPUB ==========
CLOUDPUB_EMAIL = "olebducf50@gmail.com"
CLOUDPUB_PASSWORD = "5464475337745l"

# ========== HTML страница ==========
HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>📞 Голосовой чат</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 20px;
            max-width: 1200px;
            margin: auto;
            background-color: #f5f5f5;
            display: flex;
            gap: 20px;
        }
        #leftPanel {
            flex: 2;
        }
        #rightPanel {
            flex: 1;
            background: white;
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            height: fit-content;
        }
        #status {
            padding: 15px;
            background: #e3f2fd;
            border-radius: 8px;
            margin: 15px 0;
            border-left: 4px solid #2196f3;
        }
        button {
            padding: 12px 20px;
            margin: 5px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        #callBtn {
            background: linear-gradient(135deg, #4CAF50, #2E7D32);
            color: white;
        }
        #endBtn {
            background: linear-gradient(135deg, #f44336, #c62828);
            color: white;
        }
        #acceptBtn {
            background: linear-gradient(135deg, #00c853, #64dd17);
            color: white;
        }
        #rejectBtn {
            background: linear-gradient(135deg, #ff9100, #ff6d00);
            color: white;
        }
        #muteBtn {
            background: linear-gradient(135deg, #9c27b0, #673ab7);
            color: white;
        }
        #speakerBtn {
            background: linear-gradient(135deg, #0097a7, #006064);
            color: white;
        }
        .url-box {
            background: #fff3cd;
            padding: 12px;
            border-radius: 8px;
            margin: 10px 0;
            word-break: break-all;
            border: 1px solid #ffe082;
        }
        .input-box {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            margin: 10px 0;
            box-sizing: border-box;
        }
        .incoming-call {
            background: linear-gradient(135deg, #ffeb3b, #ffc107);
            padding: 20px;
            border-radius: 10px;
            margin: 15px 0;
            text-align: center;
            display: none;
            border: 2px solid #ff9800;
        }
        .call-info {
            font-size: 18px;
            margin: 10px 0;
            color: #333;
        }
        .action-buttons {
            margin-top: 15px;
        }
        #callStatus {
            padding: 12px;
            background: #fff;
            border-radius: 8px;
            margin: 15px 0;
            min-height: 24px;
            border: 1px solid #e0e0e0;
        }
        audio {
            width: 100%;
            margin-top: 15px;
        }
        h1 {
            color: #333;
            text-align: center;
        }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .online { background: #4CAF50; }
        .offline { background: #f44336; }
        .calling { background: #2196f3; }
        
        /* Чат */
        #chatBox {
            background: white;
            border-radius: 10px;
            padding: 15px;
            margin-top: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        #chatRecipient {
            width: 100%;
            padding: 10px;
            margin-bottom: 10px;
            border: 2px solid #ddd;
            border-radius: 5px;
        }
        #messages {
            height: 250px;
            overflow-y: auto;
            border: 1px solid #ddd;
            padding: 10px;
            margin-bottom: 10px;
            background: #fafafa;
            border-radius: 5px;
            display: flex;
            flex-direction: column;
        }
        .message {
            margin: 5px 0;
            padding: 8px 12px;
            border-radius: 8px;
            max-width: 80%;
            clear: both;
            word-wrap: break-word;
        }
        .message.incoming {
            background: #e3f2fd;
            align-self: flex-start;
            border-bottom-left-radius: 2px;
        }
        .message.outgoing {
            background: #dcf8c6;
            align-self: flex-end;
            border-bottom-right-radius: 2px;
        }
        .message strong {
            color: #2196f3;
        }
        #messageInput {
            width: calc(100% - 90px);
            padding: 10px;
            border: 2px solid #ddd;
            border-radius: 5px;
            margin-right: 5px;
        }
        #sendBtn {
            width: 80px;
            padding: 10px;
            background: #2196f3;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        /* Список пользователей */
        #userList {
            list-style: none;
            padding: 0;
        }
        #userList li {
            padding: 10px;
            margin: 5px 0;
            background: #f0f0f0;
            border-radius: 5px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        #userList li:hover {
            background: #e0e0e0;
        }
        .call-icon {
            background: #4CAF50;
            color: white;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
        }
        /* Модальное окно ввода имени */
        #nameModal {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0,0,0,0.7);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
        .modal-content {
            background: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            max-width: 400px;
            width: 90%;
        }
        .modal-content input {
            width: 100%;
            padding: 12px;
            margin: 20px 0;
            border: 2px solid #2196f3;
            border-radius: 8px;
            font-size: 16px;
        }
        .modal-content button {
            background: #2196f3;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
        }
        .error-message {
            color: red;
            margin: 10px 0;
        }
        /* Управление звуком */
        .audio-controls {
            background: #fff;
            padding: 15px;
            border-radius: 10px;
            margin: 15px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: none;
        }
        .audio-controls h3 {
            margin-top: 0;
            color: #333;
        }
        .control-row {
            display: flex;
            align-items: center;
            margin: 10px 0;
            gap: 10px;
        }
        .volume-slider-container {
            flex-grow: 1;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .volume-slider {
            flex-grow: 1;
            height: 6px;
            -webkit-appearance: none;
            appearance: none;
            background: #ddd;
            border-radius: 3px;
            outline: none;
        }
        .volume-slider::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: #2196f3;
            cursor: pointer;
            border: 2px solid white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        .volume-value {
            font-weight: bold;
            color: #2196f3;
            min-width: 40px;
            text-align: right;
        }
        .control-label {
            min-width: 120px;
            font-weight: bold;
            color: #555;
        }
    </style>
</head>
<body>
    <!-- Модальное окно для ввода имени -->
    <div id="nameModal">
        <div class="modal-content">
            <h2>Введите ваше имя</h2>
            <p>Это имя будет видно другим пользователям</p>
            <input type="text" id="usernameInput" placeholder="Ваше имя" autofocus>
            <button id="setNameBtn">Продолжить</button>
            <div id="nameError" class="error-message"></div>
        </div>
    </div>

    <div id="leftPanel">
        <h1>📞 Голосовой чат</h1>
        
        <div id="status">
            <strong>Ваш ID:</strong> 
            <span id="myId">—</span>
            <span class="status-indicator offline" id="statusIndicator"></span>
        </div>
        
        <div id="cloudpubUrl" style="display:none;">
            <strong>🌐 Публичный URL:</strong>
            <div class="url-box" id="publicUrl"></div>
            <small>Отправьте эту ссылку другу</small>
        </div>
        
        <div>
            <input type="text" id="targetId" placeholder="Кому позвонить (ID)" class="input-box">
            <br>
            <button id="callBtn" disabled>📞 Позвонить</button>
            <button id="endBtn" disabled>📴 Завершить</button>
        </div>
        
        <div id="incomingCall" class="incoming-call">
            <div class="call-info">
                <strong>📱 Входящий звонок от:</strong><br>
                <span id="callerId" style="font-size: 24px; font-weight: bold;"></span>
            </div>
            <div class="action-buttons">
                <button id="acceptBtn">✅ Принять</button>
                <button id="rejectBtn">❌ Отклонить</button>
            </div>
        </div>
        
        <div id="callStatus">Статус: Ожидание регистрации...</div>
        
        <div id="audioControls" class="audio-controls">
            <h3>🎛️ Управление звуком</h3>
            <div class="control-row">
                <div class="control-label">Микрофон:</div>
                <button id="muteBtn">🎤 Вкл/Выкл</button>
            </div>
            <div class="control-row">
                <div class="control-label">Динамики:</div>
                <button id="speakerBtn">🔈 Вкл/Выкл</button>
            </div>
            <div class="control-row">
                <div class="control-label">Громкость:</div>
                <div class="volume-slider-container">
                    <span>🔊</span>
                    <input type="range" min="0" max="100" value="80" class="volume-slider" id="volumeSlider">
                    <span class="volume-value" id="volumeValue">80%</span>
                </div>
            </div>
        </div>
        
        <audio id="remoteAudio" autoplay></audio>

        <!-- Чат (приватный) -->
        <div id="chatBox">
            <h3>💬 Приватный чат</h3>
            <select id="chatRecipient">
                <option value="">-- Выберите получателя --</option>
            </select>
            <div id="messages"></div>
            <div>
                <input type="text" id="messageInput" placeholder="Введите сообщение..." disabled>
                <button id="sendBtn" disabled>Отправить</button>
            </div>
        </div>
    </div>

    <div id="rightPanel">
        <h3>👥 Онлайн</h3>
        <ul id="userList"></ul>
    </div>

    <script>
        let ws, myId, targetId, callerId, peerConnection, localStream;
        let isInitiator = false;
        let pendingOffer = null;
        let isMuted = false;
        let isSpeakerMuted = false;
        let volume = 0.8;
        let localAudioTracks = [];
        let username = localStorage.getItem('username');
        let registered = false;

        // Элементы
        const nameModal = document.getElementById('nameModal');
        const usernameInput = document.getElementById('usernameInput');
        const setNameBtn = document.getElementById('setNameBtn');
        const nameError = document.getElementById('nameError');
        const myIdSpan = document.getElementById('myId');
        const statusIndicator = document.getElementById('statusIndicator');
        const callStatus = document.getElementById('callStatus');
        const callBtn = document.getElementById('callBtn');
        const endBtn = document.getElementById('endBtn');
        const targetIdInput = document.getElementById('targetId');
        const messageInput = document.getElementById('messageInput');
        const sendBtn = document.getElementById('sendBtn');
        const messagesDiv = document.getElementById('messages');
        const userList = document.getElementById('userList');
        const chatRecipient = document.getElementById('chatRecipient');
        const incomingCallDiv = document.getElementById('incomingCall');
        const callerIdSpan = document.getElementById('callerId');
        const acceptBtn = document.getElementById('acceptBtn');
        const rejectBtn = document.getElementById('rejectBtn');
        const muteBtn = document.getElementById('muteBtn');
        const speakerBtn = document.getElementById('speakerBtn');
        const volumeSlider = document.getElementById('volumeSlider');
        const volumeValue = document.getElementById('volumeValue');
        const audioControls = document.getElementById('audioControls');
        const remoteAudio = document.getElementById('remoteAudio');

        // Если имя уже сохранено, скрываем модалку сразу
        if (username) {
            nameModal.style.display = 'none';
            connectWebSocket();
        } else {
            nameModal.style.display = 'flex';
        }

        setNameBtn.addEventListener('click', () => {
            const name = usernameInput.value.trim();
            if (!name) {
                nameError.textContent = 'Введите имя';
                return;
            }
            username = name;
            localStorage.setItem('username', username);
            nameModal.style.display = 'none';
            connectWebSocket();
        });

        usernameInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') setNameBtn.click();
        });

        function connectWebSocket() {
            ws = new WebSocket((window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/ws');
            
            ws.onopen = () => {
                console.log('✅ WebSocket подключен');
                ws.send(JSON.stringify({ type: 'register', name: username }));
            };
            
            ws.onmessage = async (e) => {
                try {
                    const data = JSON.parse(e.data);
                    console.log('Получено сообщение:', data.type);
                    
                    switch(data.type) {
                        case 'registered':
                            registered = true;
                            myId = data.name;
                            myIdSpan.textContent = myId;
                            updateStatus('Готов к звонкам', 'online');
                            callBtn.disabled = false;
                            messageInput.disabled = false;
                            sendBtn.disabled = false;
                            break;
                            
                        case 'error':
                            if (data.reason === 'name_taken') {
                                nameError.textContent = 'Имя уже занято. Выберите другое.';
                                nameModal.style.display = 'flex';
                                localStorage.removeItem('username');
                                username = null;
                            } else if (data.reason === 'user_not_online') {
                                alert(`Пользователь ${data.to} не в сети. Сообщение не доставлено.`);
                            } else {
                                alert('Ошибка: ' + data.reason);
                            }
                            break;
                            
                        case 'users':
                            updateUserList(data.users);
                            break;
                            
                        case 'private_message':
                            addMessage(data.from, data.text, 'incoming');
                            // Можно добавить звуковой сигнал
                            break;
                            
                        case 'offer':
                            handleIncomingCall(data);
                            break;
                            
                        case 'answer':
                            await handleAnswer(data);
                            break;
                            
                        case 'ice_candidate':
                            await handleIceCandidate(data);
                            break;
                            
                        case 'call_rejected':
                            handleCallRejected(data);
                            break;
                            
                        case 'call_canceled':
                            handleCallCanceled(data);
                            break;
                    }
                } catch(err) {
                    console.error('Ошибка обработки сообщения:', err);
                }
            };
            
            ws.onclose = () => {
                registered = false;
                updateStatus('Соединение потеряно', 'offline');
                callBtn.disabled = true;
                messageInput.disabled = true;
                sendBtn.disabled = true;
                setTimeout(connectWebSocket, 3000);
            };
            
            ws.onerror = () => {
                updateStatus('Ошибка соединения', 'offline');
            };
        }

        function updateUserList(users) {
            userList.innerHTML = '';
            chatRecipient.innerHTML = '<option value="">-- Выберите получателя --</option>';
            users.forEach(user => {
                if (user !== myId) {
                    const li = document.createElement('li');
                    li.innerHTML = `${user} <span class="call-icon" onclick="callUser('${user}')">📞</span>`;
                    li.onclick = () => {
                        targetIdInput.value = user;
                        chatRecipient.value = user;
                    };
                    userList.appendChild(li);
                    
                    const option = document.createElement('option');
                    option.value = user;
                    option.textContent = user;
                    chatRecipient.appendChild(option);
                } else {
                    const li = document.createElement('li');
                    li.textContent = `${user} (вы)`;
                    li.style.background = '#e3f2fd';
                    userList.appendChild(li);
                }
            });
        }

        window.callUser = function(user) {
            targetIdInput.value = user;
            startCall();
        }

        function addMessage(sender, text, type = 'incoming') {
            const msgDiv = document.createElement('div');
            msgDiv.className = `message ${type}`;
            msgDiv.innerHTML = `<strong>${sender}:</strong> ${text}`;
            messagesDiv.appendChild(msgDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function sendMessage() {
            const to = chatRecipient.value;
            const text = messageInput.value.trim();
            if (!to) {
                alert('Выберите получателя');
                return;
            }
            if (!text) return;
            ws.send(JSON.stringify({
                type: 'private_message',
                to: to,
                text: text
            }));
            addMessage(`Вы -> ${to}`, text, 'outgoing');
            messageInput.value = '';
        }

        sendBtn.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });

        async function startCall() {
            targetId = targetIdInput.value.trim();
            if (!targetId) {
                alert('Введите ID друга или выберите из списка!');
                return;
            }
            if (targetId === myId) {
                alert('Нельзя позвонить самому себе!');
                return;
            }
            
            updateStatus('Запрашиваю доступ к микрофону...', 'calling');
            
            try {
                localStream = await navigator.mediaDevices.getUserMedia({
                    audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
                    video: false
                });
                localAudioTracks = localStream.getAudioTracks();
                isInitiator = true;
                createPeerConnection();
                
                const offer = await peerConnection.createOffer({
                    offerToReceiveAudio: true,
                    offerToReceiveVideo: false
                });
                await peerConnection.setLocalDescription(offer);
                
                ws.send(JSON.stringify({
                    type: 'offer',
                    target: targetId,
                    offer: offer
                }));
                
                updateStatus(`Звоню ${targetId}...`, 'calling');
                callBtn.disabled = true;
                endBtn.disabled = false;
                targetIdInput.disabled = true;
                audioControls.style.display = 'block';
                
            } catch(err) {
                console.error('Ошибка при звонке:', err);
                alert(`Ошибка: ${err.message}`);
                resetCallState();
            }
        }
        
        function createPeerConnection() {
            const configuration = {
                iceServers: [
                    { urls: 'stun:stun.l.google.com:19302' },
                    { urls: 'stun:stun1.l.google.com:19302' },
                    { urls: 'stun:stun2.l.google.com:19302' }
                ],
                iceCandidatePoolSize: 10
            };
            
            peerConnection = new RTCPeerConnection(configuration);
            
            peerConnection.onicecandidate = (event) => {
                if (event.candidate && targetId) {
                    ws.send(JSON.stringify({
                        type: 'ice_candidate',
                        target: targetId,
                        candidate: event.candidate
                    }));
                }
            };
            
            peerConnection.ontrack = (event) => {
                if (!remoteAudio.srcObject) {
                    remoteAudio.srcObject = event.streams[0];
                    remoteAudio.volume = volume;
                    remoteAudio.muted = isSpeakerMuted;
                    updateStatus('✅ Разговор начался! Говорите...', 'online');
                }
            };
            
            peerConnection.onconnectionstatechange = () => {
                console.log('Состояние соединения:', peerConnection.connectionState);
            };
            
            if (localStream) {
                localStream.getTracks().forEach(track => {
                    peerConnection.addTrack(track, localStream);
                });
            }
        }
        
        function handleIncomingCall(data) {
            callerId = data.sender_id;
            pendingOffer = data.offer;
            callerIdSpan.textContent = callerId;
            incomingCallDiv.style.display = 'block';
            updateStatus(`Входящий звонок от ${callerId}...`, 'calling');
            
            setTimeout(() => {
                if (incomingCallDiv.style.display === 'block') {
                    rejectCall();
                }
            }, 30000);
        }
        
        async function acceptCall() {
            incomingCallDiv.style.display = 'none';
            
            try {
                if (!localStream) {
                    localStream = await navigator.mediaDevices.getUserMedia({
                        audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
                        video: false
                    });
                    localAudioTracks = localStream.getAudioTracks();
                }
                
                targetId = callerId;
                isInitiator = false;
                createPeerConnection();
                
                await peerConnection.setRemoteDescription(new RTCSessionDescription(pendingOffer));
                const answer = await peerConnection.createAnswer();
                await peerConnection.setLocalDescription(answer);
                
                ws.send(JSON.stringify({
                    type: 'answer',
                    target: targetId,
                    answer: answer
                }));
                
                callBtn.disabled = true;
                endBtn.disabled = false;
                targetIdInput.disabled = true;
                audioControls.style.display = 'block';
                updateStatus('✅ Звонок принят! Говорите...', 'online');
                
            } catch(err) {
                console.error('Ошибка при принятии звонка:', err);
                alert(`Ошибка: ${err.message}`);
                resetCallState();
            }
        }
        
        function rejectCall() {
            if (callerId) {
                ws.send(JSON.stringify({
                    type: 'call_rejected',
                    target: callerId,
                    reason: 'Звонок отклонен'
                }));
            }
            incomingCallDiv.style.display = 'none';
            pendingOffer = null;
            callerId = null;
            updateStatus('Звонок отклонен', 'online');
        }
        
        function handleCallRejected(data) {
            if (peerConnection) {
                peerConnection.close();
                peerConnection = null;
            }
            alert(`Звонок отклонен пользователем ${data.sender_id}`);
            resetCallState();
        }
        
        function handleCallCanceled(data) {
            if (incomingCallDiv.style.display === 'block') {
                incomingCallDiv.style.display = 'none';
                alert(`Звонок отменен пользователем ${data.sender_id}`);
            }
            resetCallState();
        }
        
        async function handleAnswer(data) {
            if (peerConnection) {
                await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
                updateStatus('✅ Соединение установлено! Говорите...', 'online');
            }
        }
        
        async function handleIceCandidate(data) {
            if (peerConnection && peerConnection.remoteDescription) {
                try {
                    await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
                } catch(err) {
                    console.error('Ошибка добавления ICE кандидата:', err);
                }
            }
        }
        
        function toggleMute() {
            if (localAudioTracks.length > 0) {
                isMuted = !isMuted;
                localAudioTracks.forEach(track => track.enabled = !isMuted);
                muteBtn.innerHTML = isMuted ? '🔇 Включить микрофон' : '🎤 Выключить микрофон';
                muteBtn.style.background = isMuted ? 'linear-gradient(135deg, #757575, #424242)' : 'linear-gradient(135deg, #9c27b0, #673ab7)';
            }
        }
        
        function toggleSpeaker() {
            isSpeakerMuted = !isSpeakerMuted;
            remoteAudio.muted = isSpeakerMuted;
            speakerBtn.innerHTML = isSpeakerMuted ? '🔇 Включить звук' : '🔈 Выключить звук';
            speakerBtn.style.background = isSpeakerMuted ? 'linear-gradient(135deg, #757575, #424242)' : 'linear-gradient(135deg, #0097a7, #006064)';
        }
        
        function adjustVolume(value) {
            volume = value / 100;
            remoteAudio.volume = volume;
            volumeValue.textContent = value + '%';
            const percent = (value - volumeSlider.min) / (volumeSlider.max - volumeSlider.min) * 100;
            volumeSlider.style.background = `linear-gradient(to right, #2196f3 ${percent}%, #ddd ${percent}%)`;
        }
        
        function endCall() {
            if (targetId && ws.readyState === WebSocket.OPEN) {
                if (isInitiator) {
                    ws.send(JSON.stringify({ type: 'call_canceled', target: targetId }));
                }
            }
            if (peerConnection) {
                peerConnection.close();
                peerConnection = null;
            }
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
                localStream = null;
                localAudioTracks = [];
            }
            remoteAudio.srcObject = null;
            remoteAudio.muted = false;
            remoteAudio.volume = 0.8;
            isMuted = false;
            isSpeakerMuted = false;
            volume = 0.8;
            volumeSlider.value = 80;
            adjustVolume(80);
            muteBtn.innerHTML = '🎤 Вкл/Выкл';
            muteBtn.style.background = 'linear-gradient(135deg, #9c27b0, #673ab7)';
            speakerBtn.innerHTML = '🔈 Вкл/Выкл';
            speakerBtn.style.background = 'linear-gradient(135deg, #0097a7, #006064)';
            resetCallState();
            updateStatus('Звонок завершен', 'online');
        }
        
        function resetCallState() {
            callBtn.disabled = false;
            endBtn.disabled = true;
            targetIdInput.disabled = false;
            incomingCallDiv.style.display = 'none';
            audioControls.style.display = 'none';
            targetId = null;
            callerId = null;
            pendingOffer = null;
            isInitiator = false;
        }
        
        function updateStatus(message, statusClass = '') {
            callStatus.textContent = `Статус: ${message}`;
            statusIndicator.className = 'status-indicator';
            if (statusClass) statusIndicator.classList.add(statusClass);
        }
        
        // Обработчики кнопок
        callBtn.onclick = startCall;
        endBtn.onclick = endCall;
        acceptBtn.onclick = acceptCall;
        rejectBtn.onclick = rejectCall;
        muteBtn.onclick = toggleMute;
        speakerBtn.onclick = toggleSpeaker;
        volumeSlider.oninput = () => adjustVolume(volumeSlider.value);
        
        window.addEventListener('beforeunload', (e) => {
            if (peerConnection && peerConnection.connectionState === 'connected') {
                e.preventDefault();
                e.returnValue = 'У вас активный звонок. Вы уверены?';
                return e.returnValue;
            }
        });
    </script>
</body>
</html>"""

# ========== CloudPub функция ==========
async def publish_with_cloudpub(local_port=8080):
    """Публикует локальный сервер через CloudPub"""
    global cloudpub_info
    
    try:
        print("\n🔗 Подключаюсь к CloudPub...")
        conn = Connection(email=CLOUDPUB_EMAIL, password=CLOUDPUB_PASSWORD)
        
        print(f"📡 Публикую localhost:{local_port} через CloudPub...")
        endpoint = conn.publish(
            Protocol.HTTP,
            f"localhost:{local_port}",
            name="Голосовой чат",
            auth=Auth.NONE
        )
        
        public_url = endpoint.url
        print(f"✅ Сервис опубликован! 🌐 {public_url}")
        
        # Обновляем HTML с публичным URL
        global HTML_PAGE
        HTML_PAGE = HTML_PAGE.replace(
            'id="cloudpubUrl" style="display:none;"',
            'id="cloudpubUrl"'
        ).replace(
            '<div class="url-box" id="publicUrl"></div>',
            f'<div class="url-box" id="publicUrl">{public_url}</div>'
        )
        
        cloudpub_info = {
            'connection': conn,
            'endpoint': endpoint,
            'url': public_url
        }
        return cloudpub_info
        
    except Exception as e:
        print(f"❌ Ошибка CloudPub: {e}")
        return None

# ========== Основной сервер ==========
connected_clients = {}  # имя -> websocket

async def broadcast_users():
    """Отправить всем клиентам список онлайн пользователей"""
    if not connected_clients:
        return
    users = list(connected_clients.keys())
    for ws in connected_clients.values():
        try:
            await ws.send_json({'type': 'users', 'users': users})
        except:
            pass  # клиент отвалится позже

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    # Ждём регистрационное сообщение
    try:
        msg = await ws.receive_json()
    except:
        await ws.close()
        return ws
    
    if msg.get('type') != 'register' or 'name' not in msg:
        await ws.close()
        return ws
    
    name = msg['name'].strip()
    if not name:
        await ws.send_json({'type': 'error', 'reason': 'empty_name'})
        await ws.close()
        return ws
    
    if name in connected_clients:
        await ws.send_json({'type': 'error', 'reason': 'name_taken'})
        await ws.close()
        return ws
    
    # Регистрируем клиента
    connected_clients[name] = ws
    await ws.send_json({'type': 'registered', 'name': name})
    await broadcast_users()
    
    print(f"✅ {name} подключился")
    
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    data['sender_id'] = name
                    
                    if data['type'] in ['offer', 'answer', 'ice_candidate', 'call_rejected', 'call_canceled']:
                        target = data.get('target')
                        if target in connected_clients:
                            await connected_clients[target].send_json(data)
                            print(f"  📨 {name} -> {target}: {data['type']}")
                        else:
                            if data['type'] == 'offer':
                                await ws.send_json({
                                    'type': 'call_rejected',
                                    'sender_id': target,
                                    'reason': 'Пользователь не найден'
                                })
                    
                    elif data['type'] == 'private_message':
                        to = data.get('to')
                        text = data.get('text', '')
                        if to in connected_clients:
                            await connected_clients[to].send_json({
                                'type': 'private_message',
                                'from': name,
                                'text': text
                            })
                        else:
                            await ws.send_json({
                                'type': 'error',
                                'reason': 'user_not_online',
                                'to': to
                            })
                        print(f"  💬 {name} -> {to}: {text[:30]}...")
                        
                except json.JSONDecodeError:
                    print(f"❌ Ошибка JSON от {name}")
                except Exception as e:
                    print(f"❌ Ошибка обработки сообщения от {name}: {e}")
                    
    except Exception as e:
        print(f"❌ Ошибка WebSocket у {name}: {e}")
    finally:
        if name in connected_clients:
            del connected_clients[name]
            await broadcast_users()
            print(f"👋 {name} отключился")
    
    return ws

async def http_handler(request):
    return web.Response(text=HTML_PAGE, content_type='text/html')

async def main():
    print("=" * 60)
    print("🎧 ГОЛОСОВОЙ ЧАТ С ПРИВАТНЫМ ЧАТОМ")
    print("=" * 60)
    
    app = web.Application()
    app.router.add_get('/', http_handler)
    app.router.add_get('/ws', websocket_handler)
    
    @web.middleware
    async def cors_middleware(request, handler):
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    app.middlewares.append(cors_middleware)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    LOCAL_PORT = 8080
    site = web.TCPSite(runner, '0.0.0.0', LOCAL_PORT)
    await site.start()
    
    print(f"✅ Локальный сервер: http://localhost:{LOCAL_PORT}")
    
    if CLOUDPUB_AVAILABLE:
        await publish_with_cloudpub(LOCAL_PORT)
    else:
        print("⚠️ CloudPub не установлен. Работа только в локальной сети.")
    
    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        print("\n🛑 Останавливаю сервер...")
        if cloudpub_info:
            try:
                cloudpub_info['connection'].unpublish(cloudpub_info['endpoint'].guid)
                print("✅ Публикация CloudPub удалена")
            except:
                pass

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Сервер остановлен")
        