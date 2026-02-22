# grinmain.py
import eventlet
eventlet.monkey_patch()

import time
import json
import uuid
from flask import Flask, render_template_string
from flask_sock import Sock
from cloudpub_python_sdk import Connection, Protocol, Auth

app = Flask(__name__)
sock = Sock(app)

connections = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>📞 Голосовой чат GrinMain</title>
    <style>
        /* (стили полностью совпадают с предыдущей версией) */
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
    <h1>📞 Голосовой чат GrinMain</h1>
    
    <div id="status">
        <strong>Ваш ID:</strong> 
        <span id="myId">загрузка...</span>
        <span class="status-indicator offline" id="statusIndicator"></span>
    </div>
    
    <!-- Блок для отображения публичного URL (будет заполнен сервером) -->
    <div id="cloudpubUrl" style="display: none;">
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
        let volume = 0.8;
        let localAudioTracks = [];

        // Для визуализатора
        let audioContext, analyser, source, animationFrame;
        let visualizerBars = [];

        // ========== Кеширование ICE-кандидатов ==========
        let pendingIceCandidates = [];

        // ========== Надёжная конфигурация ICE с альтернативным TURN ==========
        const iceConfiguration = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' },
                { urls: 'stun:stun2.l.google.com:19302' },
                { urls: 'stun:stun3.l.google.com:19302' },
                { urls: 'stun:stun4.l.google.com:19302' },
                // Альтернативный TURN-сервер (anyfirewall.com)
                {
                    urls: 'turn:turn.anyfirewall.com:443?transport=tcp',
                    username: 'webrtc',
                    credential: 'webrtc'
                },
                // Запасной TURN (openrelay)
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

                        case 'public_url':
                            // Показываем публичный URL, присланный сервером
                            document.getElementById('publicUrl').textContent = data.url;
                            document.getElementById('cloudpubUrl').style.display = 'block';
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

        // ========== Получение микрофона ==========
        async function getMicrophone() {
            try {
                if (localStream) return localStream;
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
                startVisualizer(stream);
                return stream;
            } catch (err) {
                console.error('❌ Ошибка доступа к микрофону:', err);
                alert('Не удалось получить доступ к микрофону. Проверьте разрешения.');
                throw err;
            }
        }

        // ========== Создание PeerConnection (без ручного трансивера) с расширенным логированием ==========
        function createPeerConnection() {
            if (peerConnection) {
                peerConnection.close();
            }
            peerConnection = new RTCPeerConnection(iceConfiguration);

            // Логирование изменений сигнального состояния
            peerConnection.onsignalingstatechange = () => {
                console.log('📶 Сигнальное состояние:', peerConnection.signalingState);
            };

            // Логирование сбора ICE-кандидатов
            peerConnection.onicegatheringstatechange = () => {
                console.log('🧊 Сбор ICE:', peerConnection.iceGatheringState);
            };

            // Обработка ICE кандидатов
            peerConnection.onicecandidate = (event) => {
                if (event.candidate && targetId) {
                    console.log('❄️ Локальный ICE кандидат:', event.candidate.type, event.candidate.address, event.candidate.protocol);
                    ws.send(JSON.stringify({
                        type: 'ice_candidate',
                        target: targetId,
                        candidate: event.candidate
                    }));
                } else {
                    console.log('✅ Сбор ICE завершён');
                }
            };

            peerConnection.oniceconnectionstatechange = () => {
                console.log('🔁 ICE состояние:', peerConnection.iceConnectionState);
                if (peerConnection.iceConnectionState === 'connected' || peerConnection.iceConnectionState === 'completed') {
                    console.log('✅ ICE соединение установлено!');
                    updateStatus('Соединение установлено', 'online');
                }
                if (peerConnection.iceConnectionState === 'failed') {
                    console.error('❌ ICE failed - возможно, нужен TURN');
                    updateStatus('Проблема сети, попробуйте ещё раз', 'offline');
                }
            };

            // Получение удалённого потока
            peerConnection.ontrack = (event) => {
                console.log('📥 Получен удалённый трек, streams:', event.streams.length);
                const audioElement = document.getElementById('remoteAudio');
                if (!audioElement.srcObject) {
                    audioElement.srcObject = event.streams[0];
                    audioElement.volume = volume;
                    audioElement.muted = isSpeakerMuted;
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
                console.log('👥 Отправители после добавления:', peerConnection.getSenders().map(s => s.track?.kind));
            } else {
                console.warn('⚠️ localStream отсутствует при создании PeerConnection');
            }

            return peerConnection;
        }

        // ========== Звонок (инициатор) ==========
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
                await getMicrophone();
                
                isInitiator = true;
                createPeerConnection();
                
                const offer = await peerConnection.createOffer();
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
            
            setTimeout(() => {
                if (document.getElementById('incomingCall').style.display === 'block') {
                    rejectCall();
                }
            }, 30000);
        }

        // ========== Принятие звонка (получатель) ==========
        async function acceptCall() {
            try {
                document.getElementById('incomingCall').style.display = 'none';
                
                await getMicrophone();
                
                targetId = callerId;
                isInitiator = false;
                createPeerConnection();
                
                // Устанавливаем удалённое описание (offer)
                await peerConnection.setRemoteDescription(new RTCSessionDescription(pendingOffer));
                console.log('📥 Remote description установлен (offer)');
                
                // Добавляем все ICE-кандидаты, полученные до установки remoteDescription
                if (pendingIceCandidates.length > 0) {
                    console.log(`🔄 Добавляю ${pendingIceCandidates.length} отложенных ICE кандидатов после установки remoteDescription`);
                    for (let candidate of pendingIceCandidates) {
                        try {
                            await peerConnection.addIceCandidate(candidate);
                            console.log('🧊 Добавлен отложенный кандидат');
                        } catch (e) {
                            console.error('❌ Ошибка добавления отложенного кандидата:', e);
                        }
                    }
                    pendingIceCandidates = [];
                }
                
                // Создаём и отправляем answer
                const answer = await peerConnection.createAnswer();
                await peerConnection.setLocalDescription(answer);
                console.log('📤 Отправляю answer');
                
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

        // ========== Обработка ответа (инициатор) ==========
        async function handleAnswer(data) {
            if (peerConnection) {
                await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
                console.log('✅ Remote description установлен (answer)');
                updateStatus('✅ Соединение установлено! Говорите...', 'online');
                
                // Добавляем отложенные ICE-кандидаты после установки remoteDescription
                if (pendingIceCandidates.length > 0) {
                    console.log(`🔄 Добавляю ${pendingIceCandidates.length} отложенных ICE кандидатов после answer`);
                    for (let candidate of pendingIceCandidates) {
                        try {
                            await peerConnection.addIceCandidate(candidate);
                            console.log('🧊 Добавлен отложенный кандидат');
                        } catch (e) {
                            console.error('❌ Ошибка добавления отложенного кандидата:', e);
                        }
                    }
                    pendingIceCandidates = [];
                }
            }
        }

        // ========== Обработка ICE-кандидатов с буферизацией ==========
        async function handleIceCandidate(data) {
            console.log('❄️ Получен удалённый ICE кандидат:', data.candidate.type, data.candidate.address, data.candidate.protocol);
            const candidate = new RTCIceCandidate(data.candidate);
            
            // Если peerConnection ещё не создан или remoteDescription не установлен – сохраняем
            if (!peerConnection || !peerConnection.remoteDescription) {
                console.log('⏳ ICE кандидат получен до remoteDescription, сохраняем');
                pendingIceCandidates.push(candidate);
                return;
            }
            
            try {
                await peerConnection.addIceCandidate(candidate);
                console.log('🧊 ICE кандидат добавлен сразу');
            } catch (err) {
                console.error('❌ Ошибка добавления ICE кандидата:', err);
            }
        }

        // ========== Управление звуком ==========
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

        // ========== Визуализация микрофона ==========
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
                    let avg = sum / bufferLength;
                    let level = Math.min(30, avg / 10);
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

        // ========== Тест микрофона ==========
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
            
            // Очищаем кеш кандидатов
            pendingIceCandidates = [];
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
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@sock.route('/ws')
def ws(ws):
    """WebSocket обработчик сигнальных сообщений."""
    client_id = str(uuid.uuid4())[:8]
    connections[client_id] = ws
    try:
        # Отправляем клиенту его ID
        ws.send(json.dumps({'type': 'your_id', 'data': client_id}))
        print(f"✅ Клиент {client_id} подключился")

        while True:
            message = ws.receive()
            if message is None:
                break
            data = json.loads(message)
            print(f"📨 От {client_id}: {data.get('type')} -> {data.get('target')}")

            target_id = data.get('target')
            if target_id and target_id in connections:
                data['sender_id'] = client_id
                connections[target_id].send(json.dumps(data))
            else:
                print(f"⚠️ Целевой клиент {target_id} не найден")

    except Exception as e:
        print(f"❌ Ошибка для клиента {client_id}: {e}")
    finally:
        if client_id in connections:
            del connections[client_id]
            print(f"🔌 Клиент {client_id} отключился")
        ws.close()

if __name__ == '__main__':
    from eventlet import wsgi, listen, spawn

    # Запускаем сервер в фоновом гринлете
    listener = listen(('0.0.0.0', 8080))
    server_greenlet = spawn(wsgi.server, listener, app)
    time.sleep(1)

    # Публикация через CloudPub
    cloudpub_conn = None
    endpoint = None
    try:
        cloudpub_conn = Connection(
            email="olebducf50@gmail.com",
            password="5464475337745l"
        )
        endpoint = cloudpub_conn.publish(
            Protocol.HTTP,
            "localhost:8080",
            name="Голосовой чат",
            auth=Auth.NONE
        )
        public_url = endpoint.url
        if public_url.startswith('tcp://'):
            host_part = public_url.replace('tcp://', '').split(':')[0]
            public_url = f"https://{host_part}"
            print(f"🌐 Публичный URL (преобразованный в HTTPS): {public_url}")
        else:
            print(f"🌐 Публичный URL: {public_url}")

        # Отправить URL всем подключённым клиентам (опционально)
        # for conn in connections.values():
        #     conn.send(json.dumps({'type': 'public_url', 'url': public_url}))
    except Exception as e:
        print(f"⚠️ Не удалось опубликовать через cloudpub: {e}")

    try:
        server_greenlet.wait()
    except KeyboardInterrupt:
        print("\n⏹️  Остановка сервера...")
    finally:
        if cloudpub_conn and endpoint:
            try:
                cloudpub_conn.unpublish(endpoint.guid)
                print("📤 Публикация отменена")
            except Exception as e:
                print(f"⚠️ Ошибка при отмене публикации: {e}")