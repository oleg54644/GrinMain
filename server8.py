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

# ========== HTML страница с улучшенным управлением звуком ==========
HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>📞 Голосовой чат (стабильная версия)</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 20px;
            max-width: 500px;
            margin: auto;
            background-color: #f5f5f5;
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
        #testMicBtn {
            background: linear-gradient(135deg, #607d8b, #455a64);
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
        
        /* Стили для управления звуком */
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
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .control-row {
            display: flex;
            align-items: center;
            margin: 10px 0;
            gap: 10px;
            flex-wrap: wrap;
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
        .volume-slider::-moz-range-thumb {
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
        .control-buttons {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            margin-top: 10px;
        }
        .icon {
            font-size: 18px;
        }
        /* Визуализация уровня звука */
        .visualizer {
            display: flex;
            align-items: center;
            gap: 5px;
            height: 30px;
            margin-top: 10px;
        }
        .visualizer-bar {
            width: 5px;
            background: #2196f3;
            border-radius: 3px;
            transition: height 0.1s;
            height: 5px;
        }
    </style>
</head>
<body>
    <h1>📞 Голосовой чат (стабильная версия)</h1>
    
    <div id="status">
        <strong>Ваш ID:</strong> 
        <span id="myId">загрузка...</span>
        <span class="status-indicator offline" id="statusIndicator"></span>
    </div>
    
    <div id="cloudpubUrl" style="display:none;">
        <strong>🌐 Публичный URL:</strong>
        <div class="url-box" id="publicUrl"></div>
        <small>Отправьте эту ссылку другу</small>
    </div>
    
    <div>
        <input type="text" id="targetId" placeholder="ID друга" class="input-box">
        <br>
        <button id="callBtn">📞 Позвонить</button>
        <button id="endBtn" disabled>📴 Завершить</button>
        <button id="testMicBtn">🎤 Проверить микрофон</button>
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
    
    <div id="callStatus">Статус: Ожидание...</div>
    
    <div id="audioControls" class="audio-controls">
        <h3>🎛️ Управление звуком</h3>
        
        <div class="control-row">
            <div class="control-label">Микрофон:</div>
            <div class="control-buttons">
                <button id="muteBtn">
                    <span class="icon">🎤</span> Вкл/Выкл
                </button>
            </div>
        </div>
        
        <div class="control-row">
            <div class="control-label">Динамики:</div>
            <div class="control-buttons">
                <button id="speakerBtn">
                    <span class="icon">🔈</span> Вкл/Выкл
                </button>
            </div>
        </div>
        
        <div class="control-row">
            <div class="control-label">Громкость:</div>
            <div class="volume-slider-container">
                <span class="icon">🔊</span>
                <input type="range" min="0" max="100" value="80" class="volume-slider" id="volumeSlider">
                <span class="volume-value" id="volumeValue">80%</span>
            </div>
        </div>

        <!-- Визуализатор уровня звука (микрофон) -->
        <div class="visualizer" id="visualizer">
            <span>🎤 Уровень:</span>
            <div id="visualizer-bars" style="display: flex; gap: 3px; align-items: center;"></div>
        </div>
    </div>
    
    <audio id="remoteAudio" autoplay></audio>

    <script>
        let ws, myId, targetId, callerId, peerConnection, localStream;
        let isInitiator = false;
        let pendingOffer = null;
        
        // Состояние звука
        let isMuted = false;
        let isSpeakerMuted = false;
        let volume = 0.8; // 80% по умолчанию
        let localAudioTracks = [];

        // Для визуализатора
        let audioContext, analyser, source, animationFrame;
        let visualizerBars = [];

        // ========== УЛУЧШЕНО: Надёжная конфигурация ICE с TURN ==========
        const iceConfiguration = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' },
                { urls: 'stun:stun2.l.google.com:19302' },
                // Публичные TURN-серверы (openrelay.metered.ca)
                { urls: 'turn:openrelay.metered.ca:80', username: 'openrelayproject', credential: 'openrelayproject' },
                { urls: 'turn:openrelay.metered.ca:443', username: 'openrelayproject', credential: 'openrelayproject' },
                { urls: 'turn:openrelay.metered.ca:443?transport=tcp', username: 'openrelayproject', credential: 'openrelayproject' }
            ],
            iceCandidatePoolSize: 10
        };

        function connectWebSocket() {
            ws = new WebSocket((window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/ws');
            
            ws.onopen = () => {
                console.log('✅ WebSocket подключен');
                updateStatus('Подключено к серверу', 'online');
            };
            
            ws.onmessage = async (e) => {
                try {
                    const data = JSON.parse(e.data);
                    console.log('📩 Получено сообщение:', data.type, data);
                    
                    switch(data.type) {
                        case 'your_id':
                            myId = data.data;
                            document.getElementById('myId').textContent = myId;
                            updateStatus('Готов к звонкам', 'online');
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
                    console.error('❌ Ошибка обработки сообщения:', err);
                }
            };
            
            ws.onclose = () => {
                console.warn('⚠️ WebSocket закрыт, переподключение...');
                updateStatus('Соединение потеряно', 'offline');
                setTimeout(connectWebSocket, 3000);
            };
            
            ws.onerror = (err) => {
                console.error('❌ Ошибка WebSocket:', err);
                updateStatus('Ошибка соединения', 'offline');
            };
        }

        // ========== УЛУЧШЕНО: Функция запроса микрофона с проверкой ==========
        async function getMicrophone() {
            try {
                if (localStream) return localStream; // уже есть
                const stream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    },
                    video: false
                });
                console.log('🎤 Микрофон получен, треков:', stream.getAudioTracks().length);
                localStream = stream;
                localAudioTracks = stream.getAudioTracks();
                // Показываем визуализатор
                startVisualizer(stream);
                return stream;
            } catch (err) {
                console.error('❌ Ошибка доступа к микрофону:', err);
                alert('Не удалось получить доступ к микрофону. Проверьте разрешения.');
                throw err;
            }
        }

        // ========== УЛУЧШЕНО: Создание PeerConnection с трансиверами ==========
        function createPeerConnection() {
            if (peerConnection) {
                peerConnection.close();
            }
            peerConnection = new RTCPeerConnection(iceConfiguration);
            
            // Явно добавляем аудиотрансивер для приёма и отправки (новый стандарт)
            if (peerConnection.addTransceiver) {
                peerConnection.addTransceiver('audio', { direction: 'sendrecv' });
                console.log('➕ Добавлен трансивер audio sendrecv');
            }

            // Обработка ICE кандидатов
            peerConnection.onicecandidate = (event) => {
                if (event.candidate && targetId) {
                    console.log('❄️ ICE кандидат:', event.candidate.type, event.candidate.address, event.candidate.protocol);
                    ws.send(JSON.stringify({
                        type: 'ice_candidate',
                        target: targetId,
                        candidate: event.candidate
                    }));
                }
            };

            // Отслеживание состояния ICE
            peerConnection.oniceconnectionstatechange = () => {
                console.log('🔁 ICE состояние:', peerConnection.iceConnectionState);
                if (peerConnection.iceConnectionState === 'failed') {
                    console.error('❌ ICE failed - возможно, нужен TURN');
                    updateStatus('Проблема сети, попробуйте ещё раз', 'offline');
                }
            };

            // Получение удаленного потока
            peerConnection.ontrack = (event) => {
                console.log('📥 Получен удалённый трек, streams:', event.streams.length);
                const audioElement = document.getElementById('remoteAudio');
                if (!audioElement.srcObject) {
                    audioElement.srcObject = event.streams[0];
                    audioElement.volume = volume;
                    audioElement.muted = isSpeakerMuted;
                    // УЛУЧШЕНО: принудительно запускаем воспроизведение (пользователь уже кликнул)
                    audioElement.play().catch(e => console.warn('⚠️ autoplay заблокирован:', e));
                    updateStatus('✅ Разговор начался! Говорите...', 'online');
                }
            };

            // Добавляем локальные треки, если есть
            if (localStream) {
                localStream.getTracks().forEach(track => {
                    peerConnection.addTrack(track, localStream);
                    console.log('➕ Локальный трек добавлен:', track.kind);
                });
            } else {
                console.warn('⚠️ localStream отсутствует при создании PeerConnection');
            }

            return peerConnection;
        }

        // ========== УЛУЧШЕНО: Звонок с предварительной проверкой микрофона ==========
        async function startCall() {
            targetId = document.getElementById('targetId').value.trim();
            if (!targetId) {
                alert('Введите ID друга!');
                return;
            }
            
            if (targetId === myId) {
                alert('Нельзя позвонить самому себе!');
                return;
            }

            updateStatus('Запрашиваю доступ к микрофону...', 'calling');
            
            try {
                await getMicrophone(); // теперь микрофон точно будет
                
                isInitiator = true;
                createPeerConnection();
                
                // УЛУЧШЕНО: Создаём предложение с явными опциями
                const offer = await peerConnection.createOffer({
                    offerToReceiveAudio: true,
                    offerToReceiveVideo: false
                });
                
                await peerConnection.setLocalDescription(offer);
                console.log('📤 Отправляю offer');
                
                ws.send(JSON.stringify({
                    type: 'offer',
                    target: targetId,
                    offer: offer
                }));
                
                updateStatus(`Звоню ${targetId}...`, 'calling');
                
                document.getElementById('callBtn').disabled = true;
                document.getElementById('endBtn').disabled = false;
                document.getElementById('targetId').disabled = true;
                document.getElementById('audioControls').style.display = 'block';
                
            } catch(err) {
                console.error('❌ Ошибка при звонке:', err);
                alert(`Ошибка: ${err.message}`);
                resetCallState();
            }
        }

        function handleIncomingCall(data) {
            callerId = data.sender_id;
            pendingOffer = data.offer;
            
            document.getElementById('callerId').textContent = callerId;
            document.getElementById('incomingCall').style.display = 'block';
            
            updateStatus(`Входящий звонок от ${callerId}...`, 'calling');
            
            // Автоматически скрываем через 30 секунд, если не ответили
            setTimeout(() => {
                if (document.getElementById('incomingCall').style.display === 'block') {
                    rejectCall();
                }
            }, 30000);
        }

        async function acceptCall() {
            try {
                document.getElementById('incomingCall').style.display = 'none';
                
                // Получаем микрофон
                await getMicrophone();
                
                targetId = callerId;
                isInitiator = false;
                createPeerConnection();
                
                // Устанавливаем удаленное описание (предложение звонящего)
                await peerConnection.setRemoteDescription(new RTCSessionDescription(pendingOffer));
                
                // Создаём ответ
                const answer = await peerConnection.createAnswer();
                await peerConnection.setLocalDescription(answer);
                
                ws.send(JSON.stringify({
                    type: 'answer',
                    target: targetId,
                    answer: answer
                }));
                
                document.getElementById('callBtn').disabled = true;
                document.getElementById('endBtn').disabled = false;
                document.getElementById('targetId').disabled = true;
                document.getElementById('audioControls').style.display = 'block';
                
                updateStatus('✅ Звонок принят! Говорите...', 'online');
                
            } catch(err) {
                console.error('❌ Ошибка при принятии звонка:', err);
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
            document.getElementById('incomingCall').style.display = 'none';
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
            if (document.getElementById('incomingCall').style.display === 'block') {
                document.getElementById('incomingCall').style.display = 'none';
                alert(`Звонок отменен пользователем ${data.sender_id}`);
            }
            resetCallState();
        }

        async function handleAnswer(data) {
            if (peerConnection) {
                await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
                console.log('✅ Remote description установлен');
                updateStatus('✅ Соединение установлено! Говорите...', 'online');
            }
        }

        async function handleIceCandidate(data) {
            if (peerConnection && peerConnection.remoteDescription) {
                try {
                    await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
                    console.log('🧊 ICE кандидат добавлен');
                } catch(err) {
                    console.error('❌ Ошибка добавления ICE кандидата:', err);
                }
            }
        }

        // ========== УЛУЧШЕНО: Функции управления звуком с обратной связью ==========
        function toggleMute() {
            if (localAudioTracks.length > 0) {
                isMuted = !isMuted;
                localAudioTracks.forEach(track => {
                    track.enabled = !isMuted;
                });
                
                const muteBtn = document.getElementById('muteBtn');
                if (isMuted) {
                    muteBtn.innerHTML = '<span class="icon">🔇</span> Включить микрофон';
                    muteBtn.style.background = 'linear-gradient(135deg, #757575, #424242)';
                } else {
                    muteBtn.innerHTML = '<span class="icon">🎤</span> Выключить микрофон';
                    muteBtn.style.background = 'linear-gradient(135deg, #9c27b0, #673ab7)';
                }
                console.log(`🎤 Микрофон ${isMuted ? 'выключен' : 'включен'}`);
            }
        }

        function toggleSpeaker() {
            const audioElement = document.getElementById('remoteAudio');
            if (audioElement) {
                isSpeakerMuted = !isSpeakerMuted;
                audioElement.muted = isSpeakerMuted;
                
                const speakerBtn = document.getElementById('speakerBtn');
                if (isSpeakerMuted) {
                    speakerBtn.innerHTML = '<span class="icon">🔇</span> Включить звук';
                    speakerBtn.style.background = 'linear-gradient(135deg, #757575, #424242)';
                } else {
                    speakerBtn.innerHTML = '<span class="icon">🔈</span> Выключить звук';
                    speakerBtn.style.background = 'linear-gradient(135deg, #0097a7, #006064)';
                }
                console.log(`🔊 Динамики ${isSpeakerMuted ? 'выключены' : 'включены'}`);
            }
        }

        function adjustVolume(value) {
            volume = value / 100;
            const audioElement = document.getElementById('remoteAudio');
            if (audioElement) {
                audioElement.volume = volume;
            }
            document.getElementById('volumeValue').textContent = `${value}%`;
            const slider = document.getElementById('volumeSlider');
            const percent = (value - slider.min) / (slider.max - slider.min) * 100;
            slider.style.background = `linear-gradient(to right, #2196f3 ${percent}%, #ddd ${percent}%)`;
            console.log(`🔊 Громкость: ${value}%`);
        }

        // ========== УЛУЧШЕНО: Визуализация уровня звука микрофона ==========
        function startVisualizer(stream) {
            if (!audioContext) {
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
                analyser = audioContext.createAnalyser();
                analyser.fftSize = 256;
                source = audioContext.createMediaStreamSource(stream);
                source.connect(analyser);
                
                const bufferLength = analyser.frequencyBinCount;
                const dataArray = new Uint8Array(bufferLength);
                
                const barsContainer = document.getElementById('visualizer-bars');
                barsContainer.innerHTML = '';
                visualizerBars = [];
                for (let i = 0; i < 20; i++) {
                    const bar = document.createElement('div');
                    bar.className = 'visualizer-bar';
                    barsContainer.appendChild(bar);
                    visualizerBars.push(bar);
                }
                
                function draw() {
                    animationFrame = requestAnimationFrame(draw);
                    analyser.getByteFrequencyData(dataArray);
                    let sum = 0;
                    for (let i = 0; i < bufferLength; i++) {
                        sum += dataArray[i];
                    }
                    let avg = sum / bufferLength; // 0-255
                    let level = Math.min(30, avg / 10); // примерная высота в px
                    visualizerBars.forEach(bar => {
                        bar.style.height = level + 'px';
                    });
                }
                draw();
            }
        }

        function stopVisualizer() {
            if (animationFrame) {
                cancelAnimationFrame(animationFrame);
                animationFrame = null;
            }
            if (source) {
                source.disconnect();
                source = null;
            }
            if (audioContext) {
                audioContext.close();
                audioContext = null;
            }
        }

        // ========== УЛУЧШЕНО: Тест микрофона (эхо) ==========
        async function testMicrophone() {
            try {
                await getMicrophone();
                alert('✅ Микрофон работает! Если вы что-то сказали, уровень на индикаторе должен меняться.');
            } catch (e) {
                alert('❌ Не удалось получить доступ к микрофону.');
            }
        }

        function endCall() {
            if (targetId && ws.readyState === WebSocket.OPEN) {
                if (isInitiator) {
                    ws.send(JSON.stringify({
                        type: 'call_canceled',
                        target: targetId
                    }));
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
            
            stopVisualizer();
            
            const audioElement = document.getElementById('remoteAudio');
            audioElement.srcObject = null;
            audioElement.muted = false;
            audioElement.volume = 0.8;
            
            isMuted = false;
            isSpeakerMuted = false;
            volume = 0.8;
            
            document.getElementById('volumeSlider').value = 80;
            document.getElementById('volumeValue').textContent = '80%';
            const slider = document.getElementById('volumeSlider');
            slider.style.background = 'linear-gradient(to right, #2196f3 80%, #ddd 80%)';
            
            document.getElementById('muteBtn').innerHTML = '<span class="icon">🎤</span> Вкл/Выкл';
            document.getElementById('muteBtn').style.background = 'linear-gradient(135deg, #9c27b0, #673ab7)';
            document.getElementById('speakerBtn').innerHTML = '<span class="icon">🔈</span> Вкл/Выкл';
            document.getElementById('speakerBtn').style.background = 'linear-gradient(135deg, #0097a7, #006064)';
            
            resetCallState();
            updateStatus('Звонок завершен', 'online');
        }

        function resetCallState() {
            document.getElementById('callBtn').disabled = false;
            document.getElementById('endBtn').disabled = true;
            document.getElementById('targetId').disabled = false;
            document.getElementById('incomingCall').style.display = 'none';
            document.getElementById('audioControls').style.display = 'none';
            
            targetId = null;
            callerId = null;
            pendingOffer = null;
            isInitiator = false;
        }

        function updateStatus(message, statusClass = '') {
            const statusElement = document.getElementById('callStatus');
            const indicator = document.getElementById('statusIndicator');
            
            statusElement.textContent = `Статус: ${message}`;
            indicator.className = 'status-indicator';
            if (statusClass) {
                indicator.classList.add(statusClass);
            }
            console.log(`📌 Статус: ${message}`);
        }

        // Инициализация
        window.onload = () => {
            connectWebSocket();
            
            document.getElementById('callBtn').onclick = startCall;
            document.getElementById('endBtn').onclick = endCall;
            document.getElementById('acceptBtn').onclick = acceptCall;
            document.getElementById('rejectBtn').onclick = rejectCall;
            document.getElementById('muteBtn').onclick = toggleMute;
            document.getElementById('speakerBtn').onclick = toggleSpeaker;
            document.getElementById('testMicBtn').onclick = testMicrophone;
            
            const volumeSlider = document.getElementById('volumeSlider');
            volumeSlider.oninput = () => adjustVolume(volumeSlider.value);
            adjustVolume(80);
            
            document.getElementById('targetId').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') startCall();
            });
            
            window.addEventListener('beforeunload', (e) => {
                if (peerConnection && peerConnection.connectionState === 'connected') {
                    e.preventDefault();
                    e.returnValue = 'У вас активный звонок. Вы уверены?';
                }
            });
        };
    </script>
</body>
</html>"""

# ========== CloudPub функция (без изменений) ==========
async def publish_with_cloudpub(local_port=8080):
    """Публикует локальный сервер через CloudPub"""
    global cloudpub_info
    
    try:
        print("\n🔗 Подключаюсь к CloudPub...")
        print(f"📧 Email: {CLOUDPUB_EMAIL}")
        print("🔑 Пароль: ************")
        
        conn = Connection(email=CLOUDPUB_EMAIL, password=CLOUDPUB_PASSWORD)
        
        print(f"📡 Публикую localhost:{local_port} через CloudPub...")
        endpoint = conn.publish(
            Protocol.HTTP,
            f"localhost:{local_port}",
            name="Голосовой чат",
            auth=Auth.NONE
        )
        
        public_url = endpoint.url
        print(f"✅ Сервис опубликован!")
        print(f"🌐 Публичный URL: {public_url}")
        print("=" * 50)
        
        # Обновляем HTML с публичным URL
        global HTML_PAGE
        html_with_url = HTML_PAGE.replace(
            'id="cloudpubUrl" style="display:none;"',
            'id="cloudpubUrl"'
        ).replace(
            '<div class="url-box" id="publicUrl"></div>',
            f'<div class="url-box" id="publicUrl">{public_url}</div>'
        )
        HTML_PAGE = html_with_url
        
        cloudpub_info = {
            'connection': conn,
            'endpoint': endpoint,
            'url': public_url
        }
        
        return cloudpub_info
        
    except Exception as e:
        print(f"❌ Ошибка CloudPub: {e}")
        print("⚠️  Сервер будет работать только в локальной сети")
        return None

# ========== Основной сервер (без изменений) ==========
connected_clients = {}
pending_calls = {}

async def http_handler(request):
    return web.Response(text=HTML_PAGE, content_type='text/html')

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    client_id = f"user_{len(connected_clients) + 1}"
    connected_clients[client_id] = ws
    
    print(f"👤 {client_id} подключился")
    
    try:
        await ws.send_json({"type": "your_id", "data": client_id})
        
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    data["sender_id"] = client_id
                    target_id = data.get("target")
                    
                    if target_id in connected_clients:
                        await connected_clients[target_id].send_json(data)
                        msg_type = data.get('type', 'unknown')
                        if msg_type in ['offer', 'answer', 'ice_candidate']:
                            print(f"  📨 {client_id} -> {target_id}: {msg_type}")
                        elif msg_type in ['call_rejected', 'call_canceled']:
                            print(f"  ❌ {client_id} -> {target_id}: {msg_type}")
                    else:
                        if data.get('type') == 'offer':
                            await ws.send_json({
                                "type": "call_rejected",
                                "sender_id": target_id,
                                "reason": "Пользователь не найден"
                            })
                        print(f"  ⚠️ Пользователь {target_id} не найден")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ Ошибка JSON у {client_id}: {e}")
                except Exception as e:
                    print(f"❌ Ошибка обработки сообщения у {client_id}: {e}")
                    
    except Exception as e:
        print(f"❌ Ошибка WebSocket у {client_id}: {e}")
    finally:
        if client_id in connected_clients:
            del connected_clients[client_id]
            
        for target_id in list(pending_calls.keys()):
            if pending_calls[target_id] == client_id:
                del pending_calls[target_id]
                if target_id in connected_clients:
                    await connected_clients[target_id].send_json({
                        "type": "call_canceled",
                        "sender_id": client_id,
                        "reason": "Пользователь отключился"
                    })
        
        print(f"👋 {client_id} отключился")
        
    return ws

async def main():
    print("=" * 60)
    print("🎧 ГОЛОСОВОЙ ЧАТ С CLOUDPUB (СТАБИЛЬНАЯ ВЕРСИЯ)")
    print("=" * 60)
    
    app = web.Application()
    app.router.add_get('/', http_handler)
    app.router.add_get('/ws', websocket_handler)
    
    async def cors_middleware(app, handler):
        async def middleware_handler(request):
            response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response
        return middleware_handler
    
    app.middlewares.append(cors_middleware)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    LOCAL_PORT = 8080
    site = web.TCPSite(runner, '0.0.0.0', LOCAL_PORT)
    await site.start()
    
    print(f"✅ ЛОКАЛЬНЫЙ СЕРВЕР ЗАПУЩЕН!")
    print(f"🌐 Локальный URL: http://localhost:{LOCAL_PORT}")
    print("=" * 60)
    
    if CLOUDPUB_AVAILABLE:
        await publish_with_cloudpub(LOCAL_PORT)
    else:
        print("⚠️  CloudPub не установлен. Установите: pip install cloudpub-python-sdk")
        print("   Звонок будет работать только в локальной сети")
        print("=" * 60)
        print("📱 Для телефона в той же Wi-Fi:")
        print("   http://ваш-IP-адрес:8080")
        print("=" * 60)
    
    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        print("\n🛑 Останавливаю сервер...")
        
        if cloudpub_info:
            try:
                print("🗑️  Удаляю публикацию CloudPub...")
                cloudpub_info['connection'].unpublish(cloudpub_info['endpoint'].guid)
                print("✅ Публикация удалена")
            except Exception as e:
                print(f"⚠️  Ошибка удаления публикации: {e}")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Сервер остановлен")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        print("\nПопробуйте:")
        print("1. Установить зависимости: pip install aiohttp cloudpub-python-sdk")
        print("2. Проверить интернет-соединение")
        print("3. Проверить учетные данные CloudPub")
        print("4. Проверить, что порт 8080 свободен")