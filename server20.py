# grinmain.py
import eventlet
eventlet.monkey_patch()

import time
import json
import uuid
import re
from flask import Flask, render_template_string
from flask_sock import Sock
from cloudpub_python_sdk import Connection, Protocol, Auth

app = Flask(__name__)
sock = Sock(app)

# connections: client_id -> {'ws': ws, 'nickname': str or None}
connections = {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Telegram-style голосовой чат</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }

        body {
            background: #e5e5e5;
            padding: 20px;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* Верхняя панель статуса */
        #status {
            background: white;
            border-radius: 12px;
            padding: 12px 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
        }

        .status-left {
            display: flex;
            align-items: center;
            gap: 20px;
            color: #2c3e50;
            flex-wrap: wrap;
        }

        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        .online { background: #2ecc71; }
        .offline { background: #95a5a6; }
        .calling { background: #f39c12; }

        #publicUrlContainer a {
            color: #27ae60;
            text-decoration: none;
            font-weight: 500;
        }

        /* Модальное окно ввода ника */
        #nameModal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 2000;
        }
        .modal-content {
            background: white;
            padding: 30px;
            border-radius: 16px;
            width: 300px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .modal-content h2 {
            margin-bottom: 20px;
            color: #2c3e50;
        }
        .modal-content input {
            width: 100%;
            padding: 10px;
            margin-bottom: 10px;
            border: 1px solid #ddd;
            border-radius: 30px;
            outline: none;
            font-size: 16px;
            text-align: center;
        }
        .modal-content button {
            background: #2ecc71;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 30px;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            font-size: 16px;
        }
        .modal-content button:hover {
            background: #27ae60;
        }
        #nameError {
            color: #e74c3c;
            margin-top: 10px;
            font-size: 14px;
        }

        /* Контейнер для входящего звонка */
        #incomingCall {
            background: linear-gradient(135deg, #2ecc71, #27ae60);
            color: white;
            padding: 20px;
            border-radius: 16px;
            margin-bottom: 20px;
            text-align: center;
            display: none;
            box-shadow: 0 4px 12px rgba(46, 204, 113, 0.3);
        }

        #incomingCall .call-info strong {
            font-weight: 600;
        }

        #incomingCall button {
            background: white;
            color: #27ae60;
            border: none;
            padding: 10px 24px;
            border-radius: 30px;
            font-weight: bold;
            margin: 10px 8px 0;
            cursor: pointer;
            transition: 0.2s;
        }
        #incomingCall button:hover {
            transform: scale(1.05);
        }

        /* Основной двухколоночный макет */
        .main-container {
            display: flex;
            gap: 20px;
            flex: 1;
        }

        /* Левая панель — список контактов */
        .contacts-panel {
            width: 320px;
            background: white;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            height: fit-content;
        }

        .contacts-panel h3 {
            color: #2c3e50;
            font-size: 18px;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        #manualCall {
            display: flex;
            gap: 8px;
            margin-bottom: 20px;
        }

        #manualNick {
            flex: 1;
            padding: 10px 12px;
            border: 1px solid #ddd;
            border-radius: 30px;
            outline: none;
            transition: 0.2s;
        }
        #manualNick:focus {
            border-color: #2ecc71;
            box-shadow: 0 0 0 3px rgba(46, 204, 113, 0.2);
        }

        #manualCallBtn {
            background: #2ecc71;
            color: white;
            border: none;
            border-radius: 30px;
            padding: 10px 18px;
            font-weight: bold;
            cursor: pointer;
            transition: 0.2s;
        }
        #manualCallBtn:hover {
            background: #27ae60;
        }

        .contact-list {
            list-style: none;
            max-height: 400px;
            overflow-y: auto;
        }

        .contact-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px;
            border-radius: 12px;
            margin-bottom: 4px;
            cursor: pointer;
            transition: background 0.2s;
        }
        .contact-item:hover {
            background: #f5f5f5;
        }
        .contact-item.selected {
            background: #e8f5e9;
            border-left: 4px solid #2ecc71;
        }

        .contact-info {
            display: flex;
            align-items: center;
            gap: 12px;
            flex: 1;
            overflow: hidden;
        }

        .contact-status {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #95a5a6;
        }
        .contact-status.online {
            background: #2ecc71;
        }

        .contact-nick {
            font-weight: 500;
            color: #2c3e50;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        .contact-call-btn {
            background: none;
            border: none;
            font-size: 20px;
            cursor: pointer;
            padding: 5px;
            border-radius: 50%;
            width: 36px;
            height: 36px;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: 0.2s;
            color: #2ecc71;
        }
        .contact-call-btn:hover {
            background: #e8f5e9;
        }

        /* Правая панель — чат */
        .chat-area {
            flex: 1;
            background: white;
            border-radius: 16px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        .chat-header {
            padding: 16px 20px;
            border-bottom: 1px solid #eee;
            font-weight: 600;
            color: #2c3e50;
            background: #fafafa;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            background: #f0f2f5;
        }

        .message {
            max-width: 65%;
            padding: 10px 14px;
            border-radius: 18px;
            word-wrap: break-word;
            position: relative;
            line-height: 1.4;
            font-size: 14px;
        }
        .message.own {
            align-self: flex-end;
            background: #2ecc71;
            color: white;
            border-bottom-right-radius: 4px;
        }
        .message.other {
            align-self: flex-start;
            background: white;
            color: #2c3e50;
            border-bottom-left-radius: 4px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        .message .time {
            font-size: 10px;
            opacity: 0.7;
            margin-left: 8px;
            float: right;
            margin-top: 2px;
        }

        .chat-input-area {
            display: flex;
            gap: 12px;
            padding: 16px 20px;
            border-top: 1px solid #eee;
            background: white;
        }

        #chatInput {
            flex: 1;
            padding: 12px 16px;
            border: 1px solid #ddd;
            border-radius: 30px;
            outline: none;
            transition: 0.2s;
        }
        #chatInput:focus {
            border-color: #2ecc71;
            box-shadow: 0 0 0 3px rgba(46, 204, 113, 0.2);
        }

        #sendChatBtn {
            background: #2ecc71;
            color: white;
            border: none;
            border-radius: 30px;
            padding: 12px 24px;
            font-weight: bold;
            cursor: pointer;
            transition: 0.2s;
        }
        #sendChatBtn:hover {
            background: #27ae60;
        }

        .no-contact {
            text-align: center;
            color: #7f8c8d;
            margin-top: 50px;
        }

        /* Панель управления звонком (появляется при звонке) */
        .call-controls {
            background: white;
            border-radius: 16px;
            padding: 20px;
            margin-top: 20px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            display: none;
        }

        .call-buttons {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
            margin-bottom: 16px;
        }

        .call-buttons button {
            border: none;
            padding: 10px 20px;
            border-radius: 30px;
            font-weight: 600;
            cursor: pointer;
            transition: 0.2s;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        #endCallBtn {
            background: #e74c3c;
            color: white;
        }
        #endCallBtn:hover {
            background: #c0392b;
        }

        #muteBtn, #speakerBtn {
            background: #ecf0f1;
            color: #2c3e50;
        }
        #muteBtn:hover, #speakerBtn:hover {
            background: #bdc3c7;
        }

        #testMicBtn {
            background: #3498db;
            color: white;
        }
        #testMicBtn:hover {
            background: #2980b9;
        }

        .audio-controls {
            display: flex;
            align-items: center;
            gap: 30px;
            flex-wrap: wrap;
        }

        .volume-slider-container {
            display: flex;
            align-items: center;
            gap: 15px;
            flex: 1;
            min-width: 200px;
        }

        .volume-slider-container span {
            color: #2c3e50;
            font-weight: 500;
        }

        #volumeSlider {
            flex: 1;
            height: 4px;
            -webkit-appearance: none;
            background: #ddd;
            border-radius: 2px;
            outline: none;
        }
        #volumeSlider::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #2ecc71;
            cursor: pointer;
            border: 2px solid white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }

        #volumeValue {
            font-weight: 600;
            color: #2ecc71;
            min-width: 40px;
        }

        .visualizer {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .visualizer span {
            color: #2c3e50;
        }
        #visualizer-bars {
            display: flex;
            gap: 3px;
            align-items: center;
        }
        .visualizer-bar {
            width: 5px;
            background: #2ecc71;
            border-radius: 3px;
            transition: height 0.1s;
            height: 5px;
        }

        #remoteAudio {
            display: none;
        }
    </style>
</head>
<body>
    <!-- Модальное окно для ввода ника -->
    <div id="nameModal">
        <div class="modal-content">
            <h2>Добро пожаловать</h2>
            <p>Введите ваш никнейм:</p>
            <input type="text" id="nicknameInput" placeholder="например, john_doe" autocomplete="off">
            <button id="joinBtn">Присоединиться</button>
            <div id="nameError"></div>
        </div>
    </div>

    <!-- Основной интерфейс -->
    <div id="status">
        <div class="status-left">
            <span id="statusText">Подключение...</span>
            <span>Ваш ник: <strong id="myNickname">загрузка...</strong></span>
            <span class="status-indicator offline" id="statusIndicator"></span>
        </div>
        <div id="publicUrlContainer" style="display: none;">
            <span>🌐 Публичный URL:</span>
            <a href="#" id="publicUrlLink" target="_blank"></a>
        </div>
    </div>

    <div id="incomingCall">
        <div class="call-info">
            <strong>📱 Входящий звонок от:</strong><br>
            <span id="callerId" style="font-size: 24px; font-weight: bold;"></span>
        </div>
        <div>
            <button id="acceptBtn">✅ Принять</button>
            <button id="rejectBtn">❌ Отклонить</button>
        </div>
    </div>

    <div class="main-container">
        <!-- Левая панель: контакты -->
        <div class="contacts-panel">
            <h3>👥 Контакты</h3>
            <div id="manualCall">
                <input type="text" id="manualNick" placeholder="Ник собеседника">
                <button id="manualCallBtn">Позвонить</button>
            </div>
            <ul class="contact-list" id="contactList"></ul>
        </div>

        <!-- Правая панель: чат -->
        <div class="chat-area">
            <div class="chat-header" id="chatHeader">Выберите контакт</div>
            <div class="chat-messages" id="chatMessages"></div>
            <div class="chat-input-area" id="chatInputArea" style="display: none;">
                <input type="text" id="chatInput" placeholder="Введите сообщение...">
                <button id="sendChatBtn">Отправить</button>
            </div>
            <div class="no-contact" id="noContactMsg">👈 Выберите контакт для начала чата</div>
        </div>
    </div>

    <!-- Панель управления звонком -->
    <div class="call-controls" id="callControls" style="display: none;">
        <div class="call-buttons">
            <button id="endCallBtn">📴 Завершить</button>
            <button id="muteBtn">🔇 Выкл. микрофон</button>
            <button id="speakerBtn">🔈 Выкл. звук</button>
            <button id="testMicBtn">🎤 Проверить микрофон</button>
        </div>
        <div class="audio-controls">
            <div class="volume-slider-container">
                <span>🔊 Громкость</span>
                <input type="range" min="0" max="100" value="80" id="volumeSlider">
                <span id="volumeValue">80%</span>
            </div>
            <div class="visualizer">
                <span>🎤 Уровень:</span>
                <div id="visualizer-bars"></div>
            </div>
        </div>
    </div>

    <audio id="remoteAudio" autoplay></audio>

    <script>
        // ---------- Глобальные переменные ----------
        let ws;
        let myNickname = null;            // текущий ник
        let contacts = {};                // { nick: { nick, online } }
        let selectedContactNick = null;    // ник выбранного для чата контакта
        let messages = {};                 // { contactNick: [{ text, time, isOwn }] }

        // Переменные для звонков
        let peerConnection = null;
        let localStream = null;
        let localAudioTracks = [];
        let targetNick = null;              // Текущий собеседник по звонку
        let isInitiator = false;
        let pendingOffer = null;
        let pendingIceCandidates = [];
        let isMuted = false;
        let isSpeakerMuted = false;
        let volume = 0.8;
        let audioContext, analyser, source, animationFrame;

        const iceConfiguration = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' },
                { urls: 'stun:stun2.l.google.com:19302' },
                { urls: 'stun:stun3.l.google.com:19302' },
                { urls: 'stun:stun4.l.google.com:19302' },
                { urls: 'turn:turn.anyfirewall.com:443?transport=tcp', username: 'webrtc', credential: 'webrtc' },
                { urls: 'turn:openrelay.metered.ca:80', username: 'openrelayproject', credential: 'openrelayproject' },
                { urls: 'turn:openrelay.metered.ca:443', username: 'openrelayproject', credential: 'openrelayproject' },
            ]
        };

        // ---------- WebSocket соединение ----------
        function connectWebSocket() {
            ws = new WebSocket((window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/ws');
            ws.onopen = () => {
                console.log('✅ WebSocket connected');
                updateStatus('Подключено к серверу', 'online');
                // Если есть сохранённый ник в localStorage, пробуем использовать его
                const saved = localStorage.getItem('nickname');
                if (saved) {
                    document.getElementById('nicknameInput').value = saved;
                    joinWithName(saved);
                }
            };
            ws.onmessage = async (e) => {
                try {
                    const data = JSON.parse(e.data);
                    console.log('📩 Получено:', data.type, data);
                    switch (data.type) {
                        case 'name_accepted':
                            handleNameAccepted(data);
                            break;
                        case 'name_rejected':
                            handleNameRejected(data);
                            break;
                        case 'user_list':
                            handleUserList(data.users);
                            break;
                        case 'user_online':
                            handleUserOnline(data.userId);
                            break;
                        case 'user_offline':
                            handleUserOffline(data.userId);
                            break;
                        case 'chat_message':
                            handleChatMessage(data);
                            break;
                        case 'public_url':
                            document.getElementById('publicUrlContainer').style.display = 'block';
                            document.getElementById('publicUrlLink').textContent = data.url;
                            document.getElementById('publicUrlLink').href = data.url;
                            break;
                        // Сигнальные сообщения для звонков
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
                        default:
                            console.warn('Неизвестный тип сообщения:', data.type);
                    }
                } catch (err) {
                    console.error('❌ Ошибка обработки:', err);
                }
            };
            ws.onclose = () => {
                console.warn('⚠️ WebSocket closed, reconnecting...');
                updateStatus('Соединение потеряно', 'offline');
                setTimeout(connectWebSocket, 3000);
            };
            ws.onerror = (err) => console.error('❌ WebSocket error:', err);
        }

        // ---------- Работа с ником ----------
        function joinWithName(name) {
            name = name.trim();
            if (!name) {
                document.getElementById('nameError').textContent = 'Имя не может быть пустым';
                return;
            }
            // Отправляем запрос на установку ника
            ws.send(JSON.stringify({ type: 'set_name', name: name }));
        }

        function handleNameAccepted(data) {
            myNickname = data.name;
            localStorage.setItem('nickname', myNickname);
            document.getElementById('myNickname').textContent = myNickname;
            document.getElementById('nameModal').style.display = 'none';
            document.getElementById('nameError').textContent = '';
            updateStatus('Имя принято', 'online');
        }

        function handleNameRejected(data) {
            if (data.reason === 'already_taken') {
                document.getElementById('nameError').textContent = 'Это имя уже занято, выберите другое';
            } else if (data.reason === 'invalid') {
                document.getElementById('nameError').textContent = 'Имя может содержать только буквы, цифры и _';
            } else {
                document.getElementById('nameError').textContent = 'Ошибка: ' + data.reason;
            }
        }

        // ---------- Обработка списка пользователей и статусов ----------
        function handleUserList(users) {
            // users - массив никнеймов онлайн пользователей (без нашего)
            // Сначала сбросим все контакты в offline
            for (let nick in contacts) {
                contacts[nick].online = false;
            }
            // Добавим новых и обновим статус
            users.forEach(nick => {
                if (!contacts[nick]) {
                    contacts[nick] = { nick, online: true };
                } else {
                    contacts[nick].online = true;
                }
            });
            renderContacts();
        }

        function handleUserOnline(nick) {
            if (!contacts[nick]) {
                contacts[nick] = { nick, online: true };
            } else {
                contacts[nick].online = true;
            }
            renderContacts();
        }

        function handleUserOffline(nick) {
            if (contacts[nick]) {
                contacts[nick].online = false;
            }
            renderContacts();
            // Если звонок с этим пользователем был активен, завершаем его
            if (targetNick === nick) {
                endCall();
            }
        }

        // ---------- Отрисовка списка контактов ----------
        function renderContacts() {
            const list = document.getElementById('contactList');
            list.innerHTML = '';
            const sortedNicks = Object.keys(contacts).sort();
            for (let nick of sortedNicks) {
                const contact = contacts[nick];
                const li = document.createElement('li');
                li.className = 'contact-item' + (selectedContactNick === nick ? ' selected' : '');
                li.setAttribute('data-nick', nick);

                const infoDiv = document.createElement('div');
                infoDiv.className = 'contact-info';
                infoDiv.onclick = (e) => {
                    e.stopPropagation();
                    selectContact(nick);
                };

                const statusSpan = document.createElement('span');
                statusSpan.className = 'contact-status ' + (contact.online ? 'online' : '');
                infoDiv.appendChild(statusSpan);

                const nickSpan = document.createElement('span');
                nickSpan.className = 'contact-nick';
                nickSpan.textContent = nick;
                infoDiv.appendChild(nickSpan);

                li.appendChild(infoDiv);

                const callBtn = document.createElement('button');
                callBtn.className = 'contact-call-btn';
                callBtn.textContent = '📞';
                callBtn.title = 'Позвонить';
                callBtn.onclick = (e) => {
                    e.stopPropagation();
                    if (!contact.online) {
                        alert('Пользователь не в сети');
                        return;
                    }
                    startCallWithNick(nick);
                };
                li.appendChild(callBtn);

                list.appendChild(li);
            }
        }

        // ---------- Выбор контакта для чата ----------
        function selectContact(nick) {
            selectedContactNick = nick;
            renderContacts(); // обновим выделение
            updateChatUI();
        }

        // ---------- Обновление интерфейса чата ----------
        function updateChatUI() {
            const header = document.getElementById('chatHeader');
            const messagesDiv = document.getElementById('chatMessages');
            const inputArea = document.getElementById('chatInputArea');
            const noContactMsg = document.getElementById('noContactMsg');

            if (!selectedContactNick || !contacts[selectedContactNick]) {
                header.textContent = 'Выберите контакт';
                messagesDiv.innerHTML = '';
                inputArea.style.display = 'none';
                noContactMsg.style.display = 'block';
                return;
            }

            const contact = contacts[selectedContactNick];
            header.textContent = `Чат с ${selectedContactNick} ${contact.online ? '🟢' : '🔴'}`;
            noContactMsg.style.display = 'none';
            inputArea.style.display = 'flex';

            const msgs = messages[selectedContactNick] || [];
            messagesDiv.innerHTML = '';
            msgs.forEach(msg => {
                const msgDiv = document.createElement('div');
                msgDiv.className = `message ${msg.isOwn ? 'own' : 'other'}`;
                msgDiv.innerHTML = `${msg.text} <span class="time">${msg.time}</span>`;
                messagesDiv.appendChild(msgDiv);
            });
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        // ---------- Отправка сообщения чата ----------
        function sendChatMessage() {
            if (!selectedContactNick) {
                alert('Выберите контакт');
                return;
            }
            const contact = contacts[selectedContactNick];
            if (!contact.online) {
                alert('Контакт не в сети, сообщение не будет доставлено');
                return;
            }
            const input = document.getElementById('chatInput');
            const text = input.value.trim();
            if (!text) return;

            addMessage(selectedContactNick, { text, isOwn: true });

            ws.send(JSON.stringify({
                type: 'chat_message',
                target: selectedContactNick,
                text: text
            }));

            input.value = '';
        }

        function addMessage(contactNick, msg) {
            if (!messages[contactNick]) messages[contactNick] = [];
            const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            messages[contactNick].push({ ...msg, time });
            if (selectedContactNick === contactNick) {
                updateChatUI();
            }
        }

        function handleChatMessage(data) {
            addMessage(data.sender_id, { text: data.text, isOwn: false });
        }

        // ---------- Звонки ----------
        async function startCallWithNick(nick) {
            if (!nick) return;
            if (nick === myNickname) {
                alert('Нельзя позвонить самому себе');
                return;
            }
            if (!contacts[nick] || !contacts[nick].online) {
                alert('Пользователь не в сети');
                return;
            }
            if (peerConnection) endCall();

            targetNick = nick;
            isInitiator = true;
            updateStatus('Запрашиваю микрофон...', 'calling');

            try {
                await getMicrophone();
                createPeerConnection();

                const offer = await peerConnection.createOffer();
                await peerConnection.setLocalDescription(offer);
                ws.send(JSON.stringify({ type: 'offer', target: targetNick, offer }));

                document.getElementById('callControls').style.display = 'block';
                updateStatus(`Звоню ${targetNick}...`, 'calling');
            } catch (err) {
                alert('Ошибка при звонке: ' + err.message);
                resetCallState();
            }
        }

        function handleIncomingCall(data) {
            if (peerConnection) {
                ws.send(JSON.stringify({ type: 'call_rejected', target: data.sender_id, reason: 'busy' }));
                return;
            }
            document.getElementById('callerId').textContent = data.sender_id;
            document.getElementById('incomingCall').style.display = 'block';
            targetNick = data.sender_id;
            pendingOffer = data.offer;
            isInitiator = false;
        }

        async function acceptCall() {
            document.getElementById('incomingCall').style.display = 'none';
            try {
                await getMicrophone();
                createPeerConnection();
                await peerConnection.setRemoteDescription(new RTCSessionDescription(pendingOffer));

                for (let cand of pendingIceCandidates) {
                    try { await peerConnection.addIceCandidate(cand); } catch (e) {}
                }
                pendingIceCandidates = [];

                const answer = await peerConnection.createAnswer();
                await peerConnection.setLocalDescription(answer);
                ws.send(JSON.stringify({ type: 'answer', target: targetNick, answer }));

                document.getElementById('callControls').style.display = 'block';
                updateStatus('Соединение устанавливается...', 'calling');
            } catch (err) {
                alert('Ошибка при приёме звонка: ' + err.message);
                endCall();
            }
        }

        function rejectCall() {
            document.getElementById('incomingCall').style.display = 'none';
            if (targetNick) {
                ws.send(JSON.stringify({ type: 'call_rejected', target: targetNick }));
            }
            targetNick = null;
        }

        async function handleAnswer(data) {
            if (peerConnection) {
                await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
                for (let cand of pendingIceCandidates) {
                    try { await peerConnection.addIceCandidate(cand); } catch (e) {}
                }
                pendingIceCandidates = [];
                updateStatus('✅ Соединено', 'online');
            }
        }

        async function handleIceCandidate(data) {
            const candidate = new RTCIceCandidate(data.candidate);
            if (!peerConnection || !peerConnection.remoteDescription) {
                pendingIceCandidates.push(candidate);
                return;
            }
            try {
                await peerConnection.addIceCandidate(candidate);
            } catch (err) {
                console.error('❌ Ошибка добавления ICE:', err);
            }
        }

        function handleCallRejected(data) {
            alert(`Звонок отклонён пользователем ${data.sender_id}`);
            endCall();
        }

        function handleCallCanceled(data) {
            document.getElementById('incomingCall').style.display = 'none';
            alert(`Звонок отменён пользователем ${data.sender_id}`);
            endCall();
        }

        function createPeerConnection() {
            if (peerConnection) peerConnection.close();
            peerConnection = new RTCPeerConnection(iceConfiguration);

            peerConnection.onicecandidate = (e) => {
                if (e.candidate && targetNick) {
                    ws.send(JSON.stringify({ type: 'ice_candidate', target: targetNick, candidate: e.candidate }));
                }
            };
            peerConnection.ontrack = (e) => {
                const audio = document.getElementById('remoteAudio');
                if (!audio.srcObject) {
                    audio.srcObject = e.streams[0];
                    audio.volume = volume;
                    audio.muted = isSpeakerMuted;
                    audio.play().catch(e => console.warn('autoplay error'));
                    updateStatus('✅ Разговор начат', 'online');
                }
            };
            if (localStream) {
                localStream.getTracks().forEach(track => peerConnection.addTrack(track, localStream));
            }
            return peerConnection;
        }

        async function getMicrophone() {
            if (localStream) return localStream;
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            localStream = stream;
            localAudioTracks = stream.getAudioTracks();
            startVisualizer(stream);
            return stream;
        }

        function startVisualizer(stream) {
            if (!audioContext) {
                audioContext = new AudioContext();
                analyser = audioContext.createAnalyser();
                source = audioContext.createMediaStreamSource(stream);
                source.connect(analyser);
                const barsContainer = document.getElementById('visualizer-bars');
                barsContainer.innerHTML = '';
                for (let i = 0; i < 20; i++) {
                    const bar = document.createElement('div');
                    bar.className = 'visualizer-bar';
                    barsContainer.appendChild(bar);
                }
                const bars = document.querySelectorAll('.visualizer-bar');
                const dataArray = new Uint8Array(analyser.frequencyBinCount);
                function draw() {
                    animationFrame = requestAnimationFrame(draw);
                    analyser.getByteFrequencyData(dataArray);
                    let sum = 0;
                    for (let i = 0; i < dataArray.length; i++) sum += dataArray[i];
                    let avg = sum / dataArray.length;
                    let level = Math.min(30, avg / 10);
                    bars.forEach(bar => bar.style.height = level + 'px');
                }
                draw();
            }
        }

        function stopVisualizer() {
            if (animationFrame) cancelAnimationFrame(animationFrame);
            if (source) source.disconnect();
            if (audioContext) audioContext.close();
            audioContext = null;
        }

        function endCall() {
            if (peerConnection) {
                peerConnection.close();
                peerConnection = null;
            }
            if (localStream) {
                localStream.getTracks().forEach(t => t.stop());
                localStream = null;
            }
            stopVisualizer();
            document.getElementById('callControls').style.display = 'none';
            document.getElementById('incomingCall').style.display = 'none';
            targetNick = null;
            isInitiator = false;
            pendingIceCandidates = [];
            updateStatus('Звонок завершён', 'online');
        }

        function resetCallState() {
            endCall();
        }

        // ---------- Управление звуком ----------
        function toggleMute() {
            if (localAudioTracks.length) {
                isMuted = !isMuted;
                localAudioTracks.forEach(t => t.enabled = !isMuted);
                document.getElementById('muteBtn').textContent = isMuted ? '🎤 Вкл. микрофон' : '🔇 Выкл. микрофон';
            }
        }

        function toggleSpeaker() {
            isSpeakerMuted = !isSpeakerMuted;
            document.getElementById('remoteAudio').muted = isSpeakerMuted;
            document.getElementById('speakerBtn').textContent = isSpeakerMuted ? '🔊 Вкл. звук' : '🔈 Выкл. звук';
        }

        function adjustVolume(val) {
            volume = val / 100;
            document.getElementById('remoteAudio').volume = volume;
            document.getElementById('volumeValue').textContent = val + '%';
        }

        // ---------- Вспомогательные функции ----------
        function updateStatus(msg, cls) {
            document.getElementById('statusText').textContent = msg;
            const ind = document.getElementById('statusIndicator');
            ind.className = 'status-indicator ' + cls;
        }

        // ---------- Инициализация ----------
        window.onload = () => {
            connectWebSocket();

            // Модальное окно ника
            document.getElementById('joinBtn').onclick = () => {
                joinWithName(document.getElementById('nicknameInput').value);
            };
            document.getElementById('nicknameInput').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') joinWithName(e.target.value);
            });

            // Кнопки звонка
            document.getElementById('manualCallBtn').onclick = () => {
                const nick = document.getElementById('manualNick').value.trim();
                if (nick) startCallWithNick(nick);
            };
            document.getElementById('acceptBtn').onclick = acceptCall;
            document.getElementById('rejectBtn').onclick = rejectCall;
            document.getElementById('endCallBtn').onclick = endCall;
            document.getElementById('muteBtn').onclick = toggleMute;
            document.getElementById('speakerBtn').onclick = toggleSpeaker;
            document.getElementById('testMicBtn').onclick = async () => {
                try { await getMicrophone(); alert('Микрофон работает'); } catch { alert('Нет доступа'); }
            };
            document.getElementById('volumeSlider').oninput = (e) => adjustVolume(e.target.value);
            adjustVolume(80);

            // Чат
            document.getElementById('sendChatBtn').onclick = sendChatMessage;
            document.getElementById('chatInput').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') sendChatMessage();
            });

            window.addEventListener('beforeunload', () => {
                if (peerConnection) endCall();
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
    """WebSocket обработчик сигнальных сообщений с поддержкой никнеймов."""
    client_id = str(uuid.uuid4())[:8]
    connections[client_id] = {'ws': ws, 'nickname': None}
    try:
        # Отправляем только приветствие (без ID)
        # Ожидаем, что клиент сам запросит установку ника
        print(f"✅ Клиент {client_id} подключился. Ожидает имя.")

        while True:
            message = ws.receive()
            if message is None:
                break
            data = json.loads(message)
            print(f"📨 От {client_id}: {data.get('type')} -> {data.get('target')}")

            if data['type'] == 'set_name':
                requested_name = data.get('name', '').strip()
                # Валидация: не пустой, только буквы, цифры и _
                if not requested_name:
                    ws.send(json.dumps({'type': 'name_rejected', 'reason': 'empty'}))
                    continue
                if not re.match(r'^[a-zA-Z0-9_]+$', requested_name):
                    ws.send(json.dumps({'type': 'name_rejected', 'reason': 'invalid'}))
                    continue
                # Проверка уникальности
                name_taken = any(conn['nickname'] == requested_name for conn in connections.values())
                if name_taken:
                    ws.send(json.dumps({'type': 'name_rejected', 'reason': 'already_taken'}))
                    continue

                # Присваиваем имя
                connections[client_id]['nickname'] = requested_name
                ws.send(json.dumps({'type': 'name_accepted', 'name': requested_name}))

                # Отправляем новому клиенту список онлайн (никнеймы)
                online_nicks = [conn['nickname'] for conn in connections.values() if conn['nickname'] is not None and conn['nickname'] != requested_name]
                ws.send(json.dumps({'type': 'user_list', 'users': online_nicks}))

                # Уведомляем всех остальных о новом пользователе
                for cid, conn in connections.items():
                    if cid != client_id and conn['nickname'] is not None:
                        try:
                            conn['ws'].send(json.dumps({'type': 'user_online', 'userId': requested_name}))
                        except:
                            pass
                continue

            # Для всех остальных сообщений требуется, чтобы имя было установлено
            if connections[client_id]['nickname'] is None:
                ws.send(json.dumps({'type': 'error', 'message': 'You must set a name first'}))
                continue

            # Обработка сигнальных сообщений
            target_nick = data.get('target')
            if target_nick:
                # Ищем соединение по никнейму
                target_conn = None
                for cid, conn in connections.items():
                    if conn['nickname'] == target_nick:
                        target_conn = conn['ws']
                        break
                if target_conn:
                    data['sender_id'] = connections[client_id]['nickname']
                    target_conn.send(json.dumps(data))
                else:
                    print(f"⚠️ Целевой никнейм {target_nick} не найден")
            else:
                # Сообщения без target игнорируем
                pass

    except Exception as e:
        print(f"❌ Ошибка для клиента {client_id}: {e}")
    finally:
        if client_id in connections:
            old_nick = connections[client_id]['nickname']
            del connections[client_id]
            if old_nick:
                # Уведомляем всех об отключении
                for cid, conn in connections.items():
                    if conn['nickname'] is not None:
                        try:
                            conn['ws'].send(json.dumps({'type': 'user_offline', 'userId': old_nick}))
                        except:
                            pass
                print(f"🔌 Клиент {client_id} ({old_nick}) отключился.")
            else:
                print(f"🔌 Клиент {client_id} отключился (без имени).")
        ws.close()

if __name__ == '__main__':
    from eventlet import wsgi, listen, spawn

    listener = listen(('0.0.0.0', 8080))
    server_greenlet = spawn(wsgi.server, listener, app)
    time.sleep(1)

    # Публикация через CloudPub (если доступно)
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

        # Рассылаем URL всем подключённым
        for conn in connections.values():
            conn['ws'].send(json.dumps({'type': 'public_url', 'url': public_url}))
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