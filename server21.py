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
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    <title>Мобильный голосовой чат</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }

        body {
            background: #e5e5e5;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        /* Верхняя панель статуса */
        #status {
            background: white;
            padding: 8px 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 14px;
            z-index: 100;
        }

        .status-left {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #2c3e50;
            flex-wrap: wrap;
        }

        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }
        .online { background: #2ecc71; }
        .offline { background: #95a5a6; }
        .calling { background: #f39c12; }

        #publicUrlContainer {
            font-size: 12px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 200px;
        }
        #publicUrlContainer a {
            color: #27ae60;
            text-decoration: none;
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
            padding: 30px 20px;
            border-radius: 16px;
            width: 280px;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .modal-content h2 {
            margin-bottom: 20px;
            color: #2c3e50;
            font-size: 22px;
        }
        .modal-content input {
            width: 100%;
            padding: 12px;
            margin-bottom: 15px;
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
            padding: 12px 20px;
            border-radius: 30px;
            font-weight: bold;
            cursor: pointer;
            width: 100%;
            font-size: 16px;
        }
        #nameError {
            color: #e74c3c;
            margin-top: 10px;
            font-size: 14px;
        }

        /* Экраны (по умолчанию скрыты, активный показывается) */
        .screen {
            display: none;
            flex: 1;
            flex-direction: column;
            background: #f0f2f5;
        }
        .screen.active {
            display: flex;
        }

        /* Общая шапка для экранов с кнопкой назад */
        .screen-header {
            background: white;
            padding: 12px 16px;
            display: flex;
            align-items: center;
            gap: 12px;
            border-bottom: 1px solid #eee;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .back-btn {
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #2c3e50;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
        }
        .back-btn:hover {
            background: #f5f5f5;
        }
        .screen-header h2 {
            font-size: 18px;
            font-weight: 600;
            color: #2c3e50;
            flex: 1;
        }

        /* Экран контактов */
        #contactsScreen .screen-header {
            justify-content: space-between;
        }
        #addContactBtn {
            background: #2ecc71;
            color: white;
            border: none;
            width: 40px;
            height: 40px;
            border-radius: 50%;
            font-size: 24px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
        }
        .contact-list {
            list-style: none;
            padding: 8px 0;
            flex: 1;
            overflow-y: auto;
        }
        .contact-item {
            display: flex;
            align-items: center;
            padding: 12px 16px;
            background: white;
            margin-bottom: 1px;
            border-bottom: 1px solid #eee;
        }
        .contact-info {
            display: flex;
            align-items: center;
            gap: 12px;
            flex: 1;
            cursor: pointer;
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
            font-size: 16px;
        }
        .contact-actions {
            display: flex;
            gap: 16px;
        }
        .contact-actions button {
            background: none;
            border: none;
            font-size: 22px;
            cursor: pointer;
            color: #2ecc71;
            padding: 6px;
            border-radius: 50%;
            width: 44px;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .contact-actions button:active {
            background: #e8f5e9;
        }

        /* Модальное окно добавления контакта */
        #addContactModal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 1500;
        }
        .add-contact-content {
            background: white;
            padding: 24px;
            border-radius: 20px;
            width: 280px;
            text-align: center;
        }
        .add-contact-content h3 {
            margin-bottom: 16px;
            color: #2c3e50;
        }
        .add-contact-content input {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 30px;
            margin-bottom: 16px;
            font-size: 16px;
            text-align: center;
        }
        .add-contact-content button {
            background: #2ecc71;
            color: white;
            border: none;
            padding: 12px;
            border-radius: 30px;
            font-weight: bold;
            width: 100%;
            font-size: 16px;
        }
        #addContactError {
            color: #e74c3c;
            margin-top: 10px;
            font-size: 14px;
        }

        /* Экран чата */
        #chatMessages {
            flex: 1;
            overflow-y: auto;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 8px;
            background: #f0f2f5;
        }
        .message {
            max-width: 80%;
            padding: 10px 14px;
            border-radius: 18px;
            word-wrap: break-word;
            line-height: 1.4;
            font-size: 15px;
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
            gap: 8px;
            padding: 12px 16px;
            background: white;
            border-top: 1px solid #eee;
        }
        #chatInput {
            flex: 1;
            padding: 12px 16px;
            border: 1px solid #ddd;
            border-radius: 30px;
            outline: none;
            font-size: 16px;
        }
        #sendChatBtn {
            background: #2ecc71;
            color: white;
            border: none;
            border-radius: 30px;
            padding: 0 20px;
            font-weight: bold;
            font-size: 16px;
        }

        /* Экран звонка */
        #callScreen .screen-header {
            background: #2c3e50;
            color: white;
        }
        #callScreen .back-btn {
            color: white;
        }
        #callStatus {
            font-size: 14px;
            font-weight: normal;
            margin-left: 8px;
        }
        .call-controls {
            flex: 1;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            padding: 24px 16px 32px;
            background: #1a2632;
            color: white;
        }
        .remote-info {
            text-align: center;
            margin-bottom: 30px;
        }
        .remote-nick {
            font-size: 28px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .remote-status {
            font-size: 14px;
            opacity: 0.8;
        }
        .call-buttons {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 16px;
            margin-bottom: 30px;
        }
        .call-buttons button {
            border: none;
            padding: 16px 20px;
            border-radius: 50px;
            font-weight: 600;
            font-size: 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            background: #34495e;
            color: white;
            min-width: 120px;
            justify-content: center;
        }
        #endCallBtn {
            background: #e74c3c;
        }
        #muteBtn.muted, #speakerBtn.muted {
            background: #7f8c8d;
        }
        .volume-control {
            display: flex;
            align-items: center;
            gap: 16px;
            background: #2c3e50;
            padding: 16px;
            border-radius: 30px;
            margin-bottom: 20px;
        }
        #volumeSlider {
            flex: 1;
            height: 4px;
            -webkit-appearance: none;
            background: #7f8c8d;
            border-radius: 2px;
        }
        #volumeSlider::-webkit-slider-thumb {
            -webkit-appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: #2ecc71;
            cursor: pointer;
        }
        #volumeValue {
            min-width: 45px;
            text-align: right;
            font-weight: 600;
            color: #2ecc71;
        }
        .visualizer {
            display: flex;
            align-items: center;
            gap: 12px;
            background: #2c3e50;
            padding: 16px;
            border-radius: 30px;
        }
        #visualizer-bars {
            display: flex;
            gap: 4px;
            align-items: center;
            flex: 1;
            justify-content: center;
        }
        .visualizer-bar {
            width: 6px;
            background: #2ecc71;
            border-radius: 3px;
            transition: height 0.1s;
            height: 5px;
        }

        /* Входящий звонок */
        #incomingCall {
            position: fixed;
            top: 20px;
            left: 16px;
            right: 16px;
            background: linear-gradient(135deg, #2ecc71, #27ae60);
            color: white;
            padding: 20px;
            border-radius: 20px;
            text-align: center;
            display: none;
            z-index: 2000;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        #incomingCall .call-info strong {
            font-size: 18px;
        }
        #incomingCall .call-info span {
            font-size: 28px;
            font-weight: bold;
            display: block;
            margin: 10px 0;
        }
        #incomingCall button {
            background: white;
            color: #27ae60;
            border: none;
            padding: 14px 30px;
            border-radius: 40px;
            font-weight: bold;
            margin: 8px 10px;
            font-size: 16px;
            min-width: 120px;
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

    <!-- Модальное окно добавления контакта -->
    <div id="addContactModal">
        <div class="add-contact-content">
            <h3>➕ Добавить контакт</h3>
            <input type="text" id="newContactNick" placeholder="Никнейм" autocomplete="off">
            <button id="confirmAddContact">Добавить</button>
            <div id="addContactError"></div>
        </div>
    </div>

    <!-- Верхняя панель статуса -->
    <div id="status">
        <div class="status-left">
            <span class="status-indicator offline" id="statusIndicator"></span>
            <span id="statusText">Подключение...</span>
            <span id="myNickname">загрузка...</span>
        </div>
        <div id="publicUrlContainer" style="display: none;">
            <a href="#" id="publicUrlLink" target="_blank">🌐 Публичный URL</a>
        </div>
    </div>

    <!-- Входящий звонок -->
    <div id="incomingCall">
        <div class="call-info">
            <strong>📱 Входящий звонок</strong>
            <span id="callerId"></span>
        </div>
        <div>
            <button id="acceptBtn">✅ Принять</button>
            <button id="rejectBtn">❌ Отклонить</button>
        </div>
    </div>

    <!-- Экран контактов -->
    <div id="contactsScreen" class="screen active">
        <div class="screen-header">
            <h2>Контакты</h2>
            <button id="addContactBtn">+</button>
        </div>
        <ul class="contact-list" id="contactList"></ul>
    </div>

    <!-- Экран чата -->
    <div id="chatScreen" class="screen">
        <div class="screen-header">
            <button class="back-btn" id="backFromChat">←</button>
            <h2 id="chatHeader">Чат</h2>
        </div>
        <div id="chatMessages"></div>
        <div class="chat-input-area">
            <input type="text" id="chatInput" placeholder="Сообщение...">
            <button id="sendChatBtn">➤</button>
        </div>
    </div>

    <!-- Экран звонка -->
    <div id="callScreen" class="screen">
        <div class="screen-header">
            <button class="back-btn" id="backFromCall">←</button>
            <h2>Звонок <span id="callStatus"></span></h2>
        </div>
        <div class="call-controls">
            <div class="remote-info">
                <div class="remote-nick" id="callRemoteNick"></div>
                <div class="remote-status" id="callRemoteStatus">Соединение...</div>
            </div>
            <div class="call-buttons">
                <button id="endCallBtn">📴 Завершить</button>
                <button id="muteBtn">🔇 Выкл. микрофон</button>
                <button id="speakerBtn">🔈 Выкл. звук</button>
                <button id="testMicBtn">🎤 Проверить</button>
            </div>
            <div class="volume-control">
                <span>🔊</span>
                <input type="range" min="0" max="100" value="80" id="volumeSlider">
                <span id="volumeValue">80%</span>
            </div>
            <div class="visualizer">
                <span>🎤 Уровень</span>
                <div id="visualizer-bars"></div>
            </div>
        </div>
    </div>

    <audio id="remoteAudio" autoplay></audio>

    <script>
        // ---------- Глобальные переменные ----------
        let ws;
        let myNickname = null;                // текущий ник
        let onlineUsers = {};                  // { nick: { online } } от сервера
        let myContacts = [];                    // массив ников, сохранённых контактов (из localStorage)
        let selectedContactNick = null;         // ник выбранного для чата
        let messages = {};                       // { contactNick: [{ text, time, isOwn }] }

        // Переменные для звонков
        let peerConnection = null;
        let localStream = null;
        let localAudioTracks = [];
        let targetNick = null;                   // текущий собеседник по звонку
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

        // ---------- Загрузка/сохранение контактов ----------
        function loadContacts() {
            const stored = localStorage.getItem('myContacts');
            if (stored) {
                try {
                    myContacts = JSON.parse(stored);
                } catch (e) {
                    myContacts = [];
                }
            } else {
                myContacts = [];
            }
        }
        function saveContacts() {
            localStorage.setItem('myContacts', JSON.stringify(myContacts));
        }

        // ---------- WebSocket ----------
        function connectWebSocket() {
            ws = new WebSocket((window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/ws');
            ws.onopen = () => {
                console.log('✅ WebSocket connected');
                updateStatus('Подключено', 'online');
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
                            console.warn('Неизвестный тип:', data.type);
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
        }

        // ---------- Работа с ником ----------
        function joinWithName(name) {
            name = name.trim();
            if (!name) {
                document.getElementById('nameError').textContent = 'Имя не может быть пустым';
                return;
            }
            ws.send(JSON.stringify({ type: 'set_name', name: name }));
        }

        function handleNameAccepted(data) {
            myNickname = data.name;
            localStorage.setItem('nickname', myNickname);
            document.getElementById('myNickname').textContent = myNickname;
            document.getElementById('nameModal').style.display = 'none';
            document.getElementById('nameError').textContent = '';
            updateStatus('Имя принято', 'online');
            loadContacts();
            renderContacts();
        }

        function handleNameRejected(data) {
            if (data.reason === 'already_taken') {
                document.getElementById('nameError').textContent = 'Это имя уже занято';
            } else if (data.reason === 'invalid') {
                document.getElementById('nameError').textContent = 'Только буквы, цифры и _';
            } else {
                document.getElementById('nameError').textContent = 'Ошибка: ' + data.reason;
            }
        }

        // ---------- Обработка пользователей онлайн ----------
        function handleUserList(users) {
            // users - массив ников онлайн (без нашего)
            onlineUsers = {};
            users.forEach(nick => onlineUsers[nick] = { online: true });
            renderContacts();
        }

        function handleUserOnline(nick) {
            onlineUsers[nick] = { online: true };
            renderContacts();
        }

        function handleUserOffline(nick) {
            if (onlineUsers[nick]) onlineUsers[nick].online = false;
            renderContacts();
            if (targetNick === nick) endCall();
        }

        // ---------- Рендер списка контактов (только те, что в myContacts) ----------
        function renderContacts() {
            const list = document.getElementById('contactList');
            list.innerHTML = '';
            const sorted = [...myContacts].sort();
            for (let nick of sorted) {
                const online = onlineUsers[nick] ? onlineUsers[nick].online : false;
                const li = document.createElement('li');
                li.className = 'contact-item';

                const infoDiv = document.createElement('div');
                infoDiv.className = 'contact-info';
                infoDiv.onclick = () => openChat(nick);  // переход в чат по клику на имя

                const statusSpan = document.createElement('span');
                statusSpan.className = 'contact-status ' + (online ? 'online' : '');
                infoDiv.appendChild(statusSpan);

                const nickSpan = document.createElement('span');
                nickSpan.className = 'contact-nick';
                nickSpan.textContent = nick;
                infoDiv.appendChild(nickSpan);

                li.appendChild(infoDiv);

                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'contact-actions';

                // Кнопка чата
                const chatBtn = document.createElement('button');
                chatBtn.innerHTML = '💬';
                chatBtn.title = 'Чат';
                chatBtn.onclick = (e) => {
                    e.stopPropagation();
                    openChat(nick);
                };
                actionsDiv.appendChild(chatBtn);

                // Кнопка звонка
                const callBtn = document.createElement('button');
                callBtn.innerHTML = '📞';
                callBtn.title = 'Позвонить';
                callBtn.onclick = (e) => {
                    e.stopPropagation();
                    if (!online) {
                        alert('Пользователь не в сети');
                        return;
                    }
                    startCallWithNick(nick);
                };
                actionsDiv.appendChild(callBtn);

                li.appendChild(actionsDiv);
                list.appendChild(li);
            }
        }

        // ---------- Добавление контакта ----------
        function showAddContactModal() {
            document.getElementById('addContactModal').style.display = 'flex';
            document.getElementById('newContactNick').value = '';
            document.getElementById('addContactError').textContent = '';
        }

        function addContact() {
            const nick = document.getElementById('newContactNick').value.trim();
            if (!nick) {
                document.getElementById('addContactError').textContent = 'Введите ник';
                return;
            }
            if (nick === myNickname) {
                document.getElementById('addContactError').textContent = 'Нельзя добавить себя';
                return;
            }
            if (myContacts.includes(nick)) {
                document.getElementById('addContactError').textContent = 'Уже есть в контактах';
                return;
            }
            myContacts.push(nick);
            saveContacts();
            renderContacts();
            document.getElementById('addContactModal').style.display = 'none';
        }

        // ---------- Чат ----------
        function openChat(nick) {
            selectedContactNick = nick;
            document.getElementById('chatHeader').textContent = nick;
            // Переключиться на экран чата
            document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
            document.getElementById('chatScreen').classList.add('active');
            updateChatUI();
        }

        function updateChatUI() {
            const messagesDiv = document.getElementById('chatMessages');
            if (!selectedContactNick) return;

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

        function sendChatMessage() {
            if (!selectedContactNick) return;
            if (!onlineUsers[selectedContactNick] || !onlineUsers[selectedContactNick].online) {
                alert('Контакт не в сети');
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
            // Если этот контакт не в списке контактов, можно автоматически добавить? Нет, только по желанию.
        }

        // ---------- Звонки ----------
        async function startCallWithNick(nick) {
            if (!nick) return;
            if (nick === myNickname) {
                alert('Нельзя позвонить себе');
                return;
            }
            if (!onlineUsers[nick] || !onlineUsers[nick].online) {
                alert('Пользователь не в сети');
                return;
            }
            if (peerConnection) endCall();

            targetNick = nick;
            isInitiator = true;
            updateStatus('Звонок...', 'calling');
            document.getElementById('callRemoteNick').textContent = nick;
            document.getElementById('callRemoteStatus').textContent = 'Вызов...';
            document.getElementById('callStatus').textContent = '';

            try {
                await getMicrophone();
                createPeerConnection();

                const offer = await peerConnection.createOffer();
                await peerConnection.setLocalDescription(offer);
                ws.send(JSON.stringify({ type: 'offer', target: targetNick, offer }));

                // Перейти на экран звонка
                document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
                document.getElementById('callScreen').classList.add('active');
            } catch (err) {
                alert('Ошибка: ' + err.message);
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

                document.getElementById('callRemoteNick').textContent = targetNick;
                document.getElementById('callRemoteStatus').textContent = 'Соединение...';
                document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
                document.getElementById('callScreen').classList.add('active');
            } catch (err) {
                alert('Ошибка: ' + err.message);
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
                document.getElementById('callRemoteStatus').textContent = 'Разговор';
                updateStatus('Соединено', 'online');
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
            } catch (err) {}
        }

        function handleCallRejected(data) {
            alert(`Звонок отклонён`);
            endCall();
        }

        function handleCallCanceled(data) {
            document.getElementById('incomingCall').style.display = 'none';
            alert(`Звонок отменён`);
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
                    audio.play().catch(() => {});
                    document.getElementById('callRemoteStatus').textContent = 'Разговор';
                    updateStatus('Разговор', 'online');
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
            document.getElementById('incomingCall').style.display = 'none';
            targetNick = null;
            isInitiator = false;
            pendingIceCandidates = [];
            updateStatus('Звонок завершён', 'online');
            // Вернуться на экран контактов
            document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
            document.getElementById('contactsScreen').classList.add('active');
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

        // ---------- Вспомогательные ----------
        function updateStatus(msg, cls) {
            document.getElementById('statusText').textContent = msg;
            document.getElementById('statusIndicator').className = 'status-indicator ' + cls;
        }

        // ---------- Навигация ----------
        function goToContacts() {
            document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
            document.getElementById('contactsScreen').classList.add('active');
            if (peerConnection) endCall();  // завершить звонок при возврате
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

            // Добавление контакта
            document.getElementById('addContactBtn').onclick = showAddContactModal;
            document.getElementById('confirmAddContact').onclick = addContact;
            document.getElementById('addContactModal').addEventListener('click', (e) => {
                if (e.target === document.getElementById('addContactModal')) {
                    document.getElementById('addContactModal').style.display = 'none';
                }
            });

            // Кнопки звонка
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

            // Навигация назад
            document.getElementById('backFromChat').onclick = goToContacts;
            document.getElementById('backFromCall').onclick = endCall;  // завершить и вернуться

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
        print(f"✅ Клиент {client_id} подключился. Ожидает имя.")

        while True:
            message = ws.receive()
            if message is None:
                break
            data = json.loads(message)
            print(f"📨 От {client_id}: {data.get('type')} -> {data.get('target')}")

            if data['type'] == 'set_name':
                requested_name = data.get('name', '').strip()
                if not requested_name:
                    ws.send(json.dumps({'type': 'name_rejected', 'reason': 'empty'}))
                    continue
                if not re.match(r'^[a-zA-Z0-9_]+$', requested_name):
                    ws.send(json.dumps({'type': 'name_rejected', 'reason': 'invalid'}))
                    continue
                name_taken = any(conn['nickname'] == requested_name for conn in connections.values())
                if name_taken:
                    ws.send(json.dumps({'type': 'name_rejected', 'reason': 'already_taken'}))
                    continue

                connections[client_id]['nickname'] = requested_name
                ws.send(json.dumps({'type': 'name_accepted', 'name': requested_name}))

                online_nicks = [conn['nickname'] for conn in connections.values() if conn['nickname'] is not None and conn['nickname'] != requested_name]
                ws.send(json.dumps({'type': 'user_list', 'users': online_nicks}))

                for cid, conn in connections.items():
                    if cid != client_id and conn['nickname'] is not None:
                        try:
                            conn['ws'].send(json.dumps({'type': 'user_online', 'userId': requested_name}))
                        except:
                            pass
                continue

            if connections[client_id]['nickname'] is None:
                ws.send(json.dumps({'type': 'error', 'message': 'You must set a name first'}))
                continue

            target_nick = data.get('target')
            if target_nick:
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
                pass

    except Exception as e:
        print(f"❌ Ошибка для клиента {client_id}: {e}")
    finally:
        if client_id in connections:
            old_nick = connections[client_id]['nickname']
            del connections[client_id]
            if old_nick:
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
                
