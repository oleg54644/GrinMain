import asyncio
import json
import uuid
from datetime import datetime
from aiohttp import web
from collections import defaultdict

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

# ========== HTML страница для конференц-связи ==========
HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🎙️ Конференц-связь</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50, #4a6491);
            color: white;
            padding: 25px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 32px;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }
        
        .header h1 i {
            font-size: 36px;
        }
        
        .main-content {
            display: flex;
            min-height: 600px;
        }
        
        .sidebar {
            width: 300px;
            background: #f8f9fa;
            padding: 25px;
            border-right: 1px solid #e0e0e0;
        }
        
        .content {
            flex: 1;
            padding: 25px;
            background: #fff;
        }
        
        .card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
            border: 1px solid #e0e0e0;
        }
        
        .card-title {
            font-size: 18px;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .card-title i {
            font-size: 20px;
            color: #667eea;
        }
        
        .input-group {
            margin-bottom: 15px;
        }
        
        .input-group label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        
        .input-field {
            width: 100%;
            padding: 14px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            transition: all 0.3s;
        }
        
        .input-field:focus {
            border-color: #667eea;
            outline: none;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .btn {
            width: 100%;
            padding: 15px;
            border: none;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            margin-bottom: 10px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 7px 14px rgba(0,0,0,0.1);
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        
        .btn-success {
            background: linear-gradient(135deg, #00b09b, #96c93d);
            color: white;
        }
        
        .btn-danger {
            background: linear-gradient(135deg, #ff416c, #ff4b2b);
            color: white;
        }
        
        .btn-warning {
            background: linear-gradient(135deg, #f7971e, #ffd200);
            color: white;
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .participants-list {
            margin-top: 20px;
            max-height: 300px;
            overflow-y: auto;
        }
        
        .participant-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 15px;
            margin-bottom: 8px;
            background: #f8f9fa;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
            transition: all 0.3s;
        }
        
        .participant-item:hover {
            background: #eef2ff;
            transform: translateX(5px);
        }
        
        .participant-info {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .participant-avatar {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 18px;
        }
        
        .participant-name {
            font-weight: 500;
            color: #333;
        }
        
        .participant-status {
            font-size: 12px;
            color: #666;
            margin-top: 2px;
        }
        
        .participant-muted {
            color: #ff416c;
            font-size: 14px;
        }
        
        .conference-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .participant-video {
            background: #2c3e50;
            border-radius: 15px;
            overflow: hidden;
            position: relative;
            min-height: 200px;
            border: 3px solid transparent;
            transition: all 0.3s;
        }
        
        .participant-video.active-speaker {
            border-color: #00b09b;
            box-shadow: 0 0 20px rgba(0, 176, 155, 0.3);
        }
        
        .video-info {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: linear-gradient(transparent, rgba(0,0,0,0.7));
            color: white;
            padding: 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .video-name {
            font-weight: 600;
            font-size: 16px;
        }
        
        .video-controls {
            display: flex;
            gap: 10px;
        }
        
        .control-btn {
            width: 36px;
            height: 36px;
            border-radius: 50%;
            border: none;
            background: rgba(255,255,255,0.2);
            color: white;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s;
        }
        
        .control-btn:hover {
            background: rgba(255,255,255,0.3);
            transform: scale(1.1);
        }
        
        .self-video {
            position: relative;
            border: 3px solid #667eea;
        }
        
        .self-label {
            position: absolute;
            top: 10px;
            left: 10px;
            background: #667eea;
            color: white;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .audio-visualizer {
            position: absolute;
            bottom: 60px;
            left: 0;
            right: 0;
            height: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 2px;
        }
        
        .bar {
            width: 3px;
            background: #00b09b;
            border-radius: 3px;
            animation: pulse 1s ease-in-out infinite;
        }
        
        @keyframes pulse {
            0%, 100% { height: 5px; }
            50% { height: 20px; }
        }
        
        .notification {
            position: fixed;
            top: 20px;
            right: 20px;
            background: white;
            padding: 15px 25px;
            border-radius: 10px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            display: flex;
            align-items: center;
            gap: 15px;
            transform: translateX(400px);
            transition: transform 0.3s;
            z-index: 1000;
        }
        
        .notification.show {
            transform: translateX(0);
        }
        
        .notification-icon {
            font-size: 24px;
        }
        
        .notification-success {
            border-left: 4px solid #00b09b;
        }
        
        .notification-warning {
            border-left: 4px solid #f7971e;
        }
        
        .notification-info {
            border-left: 4px solid #667eea;
        }
        
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.7);
            z-index: 2000;
            align-items: center;
            justify-content: center;
        }
        
        .modal-content {
            background: white;
            border-radius: 20px;
            padding: 30px;
            max-width: 500px;
            width: 90%;
            animation: modalIn 0.3s;
        }
        
        @keyframes modalIn {
            from {
                opacity: 0;
                transform: translateY(-50px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .modal-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        
        .modal-title {
            font-size: 24px;
            color: #2c3e50;
        }
        
        .close-modal {
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #666;
        }
        
        .conference-id {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            font-family: monospace;
            font-size: 18px;
            text-align: center;
            margin: 20px 0;
            border: 2px dashed #667eea;
        }
        
        .status-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            background: rgba(44, 62, 80, 0.9);
            color: white;
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 100;
        }
        
        .status-info {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .status-indicator {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }
        
        .status-online {
            background: #00b09b;
        }
        
        .status-offline {
            background: #ff416c;
        }
        
        .status-connecting {
            background: #f7971e;
            animation: blink 1s infinite;
        }
        
        @keyframes blink {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .volume-control {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .volume-slider {
            width: 100px;
        }
        
        .invite-section {
            margin-top: 20px;
        }
        
        .invite-link {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 10px;
            font-family: monospace;
            word-break: break-all;
            margin: 10px 0;
            border: 1px dashed #ccc;
        }
        
        .copy-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        
        .timer {
            font-family: monospace;
            font-size: 18px;
            background: rgba(0,0,0,0.2);
            padding: 5px 10px;
            border-radius: 5px;
        }
        
        @media (max-width: 768px) {
            .main-content {
                flex-direction: column;
            }
            
            .sidebar {
                width: 100%;
                border-right: none;
                border-bottom: 1px solid #e0e0e0;
            }
            
            .conference-grid {
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            }
        }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <i class="fas fa-users"></i>
                Конференц-связь
                <i class="fas fa-microphone-alt"></i>
            </h1>
            <p>Групповой голосовой чат с поддержкой до 10 участников</p>
        </div>
        
        <div class="main-content">
            <div class="sidebar">
                <div class="card">
                    <div class="card-title">
                        <i class="fas fa-user"></i>
                        Ваш профиль
                    </div>
                    <div class="input-group">
                        <label for="userName">
                            <i class="fas fa-id-card"></i>
                            Ваше имя
                        </label>
                        <input type="text" id="userName" class="input-field" placeholder="Введите ваше имя" value="Участник">
                    </div>
                    <div class="input-group">
                        <label>
                            <i class="fas fa-id-badge"></i>
                            Ваш ID
                        </label>
                        <div style="background: #f0f0f0; padding: 10px; border-radius: 8px; font-family: monospace; text-align: center;" id="userId">
                            Загрузка...
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-title">
                        <i class="fas fa-video"></i>
                        Управление конференцией
                    </div>
                    <button id="createConferenceBtn" class="btn btn-primary">
                        <i class="fas fa-plus-circle"></i>
                        Создать конференцию
                    </button>
                    <div class="input-group">
                        <label for="conferenceId">
                            <i class="fas fa-door-open"></i>
                            ID конференции
                        </label>
                        <input type="text" id="conferenceId" class="input-field" placeholder="Введите ID для присоединения">
                    </div>
                    <button id="joinConferenceBtn" class="btn btn-success">
                        <i class="fas fa-sign-in-alt"></i>
                        Присоединиться
                    </button>
                    <button id="leaveConferenceBtn" class="btn btn-danger" disabled>
                        <i class="fas fa-sign-out-alt"></i>
                        Покинуть конференцию
                    </button>
                </div>
                
                <div class="card">
                    <div class="card-title">
                        <i class="fas fa-users-cog"></i>
                        Управление звуком
                    </div>
                    <button id="muteBtn" class="btn btn-warning">
                        <i class="fas fa-microphone"></i>
                        Выключить микрофон
                    </button>
                    <div class="volume-control">
                        <i class="fas fa-volume-up"></i>
                        <input type="range" id="volumeSlider" class="volume-slider" min="0" max="100" value="100">
                    </div>
                </div>
                
                <div class="card">
                    <div class="card-title">
                        <i class="fas fa-user-friends"></i>
                        Участники (<span id="participantsCount">0</span>)
                    </div>
                    <div class="participants-list" id="participantsList">
                        <!-- Список участников будет здесь -->
                    </div>
                </div>
            </div>
            
            <div class="content">
                <div class="card">
                    <div class="card-title">
                        <i class="fas fa-broadcast-tower"></i>
                        Конференция
                        <div class="timer" id="conferenceTimer">00:00</div>
                    </div>
                    
                    <div id="conferenceArea">
                        <div id="noConferenceMessage" style="text-align: center; padding: 40px; color: #666;">
                            <i class="fas fa-users" style="font-size: 60px; margin-bottom: 20px; color: #e0e0e0;"></i>
                            <h3 style="margin-bottom: 10px;">Конференция не активна</h3>
                            <p>Создайте новую конференцию или присоединитесь к существующей</p>
                        </div>
                        
                        <div id="conferenceGrid" class="conference-grid" style="display: none;">
                            <!-- Видео блоки участников будут здесь -->
                        </div>
                    </div>
                </div>
                
                <div id="inviteSection" class="invite-section" style="display: none;">
                    <div class="card">
                        <div class="card-title">
                            <i class="fas fa-share-alt"></i>
                            Пригласить участников
                        </div>
                        <p>Отправьте эту ссылку участникам:</p>
                        <div class="invite-link" id="inviteLink">
                            Загрузка...
                        </div>
                        <button id="copyLinkBtn" class="copy-btn">
                            <i class="fas fa-copy"></i>
                            Копировать ссылку
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Модальное окно создания конференции -->
    <div id="createConferenceModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="modal-title">
                    <i class="fas fa-users"></i>
                    Создание конференции
                </h3>
                <button class="close-modal" id="closeCreateModal">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <p>Ваша конференция успешно создана!</p>
            <p>ID конференции:</p>
            <div class="conference-id" id="generatedConferenceId">
                Загрузка...
            </div>
            <p>Отправьте этот ID другим участникам или используйте ссылку ниже:</p>
            <div class="invite-link" id="modalInviteLink">
                Загрузка...
            </div>
            <button id="startConferenceBtn" class="btn btn-success" style="margin-top: 20px;">
                <i class="fas fa-play-circle"></i>
                Начать конференцию
            </button>
        </div>
    </div>
    
    <!-- Модальное окно входящего приглашения -->
    <div id="inviteModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="modal-title">
                    <i class="fas fa-phone-volume"></i>
                    Входящее приглашение
                </h3>
            </div>
            <p>Пользователь <strong id="inviterName">Имя</strong> приглашает вас в конференцию</p>
            <div class="conference-id" id="inviteConferenceId">
                ID: Загрузка...
            </div>
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                <button id="acceptInviteBtn" class="btn btn-success" style="flex: 1;">
                    <i class="fas fa-check-circle"></i>
                    Принять
                </button>
                <button id="declineInviteBtn" class="btn btn-danger" style="flex: 1;">
                    <i class="fas fa-times-circle"></i>
                    Отклонить
                </button>
            </div>
        </div>
    </div>
    
    <!-- Уведомления -->
    <div id="notification" class="notification">
        <div class="notification-icon">
            <i class="fas fa-info-circle"></i>
        </div>
        <div class="notification-content">
            <div class="notification-title">Уведомление</div>
            <div class="notification-message" id="notificationMessage">Текст уведомления</div>
        </div>
    </div>
    
    <!-- Строка состояния -->
    <div class="status-bar">
        <div class="status-info">
            <div class="status-item">
                <div class="status-indicator status-offline" id="connectionStatus"></div>
                <span>Соединение: <span id="connectionText">Отключено</span></span>
            </div>
            <div class="status-item">
                <i class="fas fa-microphone"></i>
                <span>Микрофон: <span id="micStatus">Выкл</span></span>
            </div>
            <div class="status-item">
                <i class="fas fa-user-friends"></i>
                <span>Участников: <span id="onlineCount">0</span></span>
            </div>
        </div>
        <div class="timer" id="callTimer">--:--</div>
    </div>

    <script>
        // Глобальные переменные
        let ws = null;
        let userId = null;
        let userName = "Участник";
        let conferenceId = null;
        let conferenceParticipants = new Map(); // Map(participantId -> {name, audioElement, stream, muted, volume})
        let peerConnections = new Map(); // Map(participantId -> RTCPeerConnection)
        let localStream = null;
        let isMuted = false;
        let isInConference = false;
        let conferenceStartTime = null;
        let timerInterval = null;
        let activeSpeaker = null;
        let audioContext = null;
        let analysers = new Map();
        
        // Элементы DOM
        const elements = {
            userId: document.getElementById('userId'),
            userName: document.getElementById('userName'),
            createConferenceBtn: document.getElementById('createConferenceBtn'),
            joinConferenceBtn: document.getElementById('joinConferenceBtn'),
            leaveConferenceBtn: document.getElementById('leaveConferenceBtn'),
            conferenceId: document.getElementById('conferenceId'),
            muteBtn: document.getElementById('muteBtn'),
            volumeSlider: document.getElementById('volumeSlider'),
            participantsCount: document.getElementById('participantsCount'),
            participantsList: document.getElementById('participantsList'),
            conferenceGrid: document.getElementById('conferenceGrid'),
            noConferenceMessage: document.getElementById('noConferenceMessage'),
            conferenceTimer: document.getElementById('conferenceTimer'),
            callTimer: document.getElementById('callTimer'),
            connectionStatus: document.getElementById('connectionStatus'),
            connectionText: document.getElementById('connectionText'),
            micStatus: document.getElementById('micStatus'),
            onlineCount: document.getElementById('onlineCount'),
            inviteSection: document.getElementById('inviteSection'),
            inviteLink: document.getElementById('inviteLink'),
            copyLinkBtn: document.getElementById('copyLinkBtn'),
            
            // Модальные окна
            createConferenceModal: document.getElementById('createConferenceModal'),
            generatedConferenceId: document.getElementById('generatedConferenceId'),
            modalInviteLink: document.getElementById('modalInviteLink'),
            startConferenceBtn: document.getElementById('startConferenceBtn'),
            closeCreateModal: document.getElementById('closeCreateModal'),
            
            inviteModal: document.getElementById('inviteModal'),
            inviterName: document.getElementById('inviterName'),
            inviteConferenceId: document.getElementById('inviteConferenceId'),
            acceptInviteBtn: document.getElementById('acceptInviteBtn'),
            declineInviteBtn: document.getElementById('declineInviteBtn'),
            
            // Уведомления
            notification: document.getElementById('notification'),
            notificationMessage: document.getElementById('notificationMessage')
        };
        
        // Инициализация
        function init() {
            connectWebSocket();
            setupEventListeners();
            updateStatusBar();
        }
        
        // Подключение к WebSocket
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = protocol + '//' + window.location.host + '/ws';
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = () => {
                console.log('✅ WebSocket подключен');
                updateConnectionStatus('connected', 'Подключено');
                showNotification('Соединение установлено', 'success');
            };
            
            ws.onmessage = async (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('Получено сообщение:', data.type, data);
                    
                    switch(data.type) {
                        case 'your_id':
                            handleYourId(data);
                            break;
                        case 'conference_created':
                            handleConferenceCreated(data);
                            break;
                        case 'conference_joined':
                            handleConferenceJoined(data);
                            break;
                        case 'participant_joined':
                            handleParticipantJoined(data);
                            break;
                        case 'participant_left':
                            handleParticipantLeft(data);
                            break;
                        case 'participant_updated':
                            handleParticipantUpdated(data);
                            break;
                        case 'offer':
                            handleOffer(data);
                            break;
                        case 'answer':
                            handleAnswer(data);
                            break;
                        case 'ice_candidate':
                            handleIceCandidate(data);
                            break;
                        case 'invite_to_conference':
                            handleInvite(data);
                            break;
                        case 'conference_info':
                            handleConferenceInfo(data);
                            break;
                        case 'error':
                            handleError(data);
                            break;
                    }
                } catch (error) {
                    console.error('Ошибка обработки сообщения:', error);
                }
            };
            
            ws.onclose = () => {
                console.log('❌ WebSocket отключен');
                updateConnectionStatus('disconnected', 'Отключено');
                showNotification('Соединение потеряно', 'warning');
                
                // Попытка переподключения через 3 секунды
                setTimeout(() => {
                    console.log('🔄 Попытка переподключения...');
                    connectWebSocket();
                }, 3000);
            };
            
            ws.onerror = (error) => {
                console.error('❌ WebSocket ошибка:', error);
                updateConnectionStatus('error', 'Ошибка');
                showNotification('Ошибка соединения', 'danger');
            };
        }
        
        // Настройка обработчиков событий
        function setupEventListeners() {
            // Обновление имени пользователя
            elements.userName.addEventListener('input', (e) => {
                userName = e.target.value || 'Участник';
                if (isInConference && ws) {
                    ws.send(JSON.stringify({
                        type: 'update_participant',
                        conference_id: conferenceId,
                        name: userName
                    }));
                }
                updateLocalParticipantDisplay();
            });
            
            // Создание конференции
            elements.createConferenceBtn.addEventListener('click', createConference);
            
            // Присоединение к конференции
            elements.joinConferenceBtn.addEventListener('click', joinConference);
            
            // Выход из конференции
            elements.leaveConferenceBtn.addEventListener('click', leaveConference);
            
            // Кнопка микрофона
            elements.muteBtn.addEventListener('click', toggleMicrophone);
            
            // Регулятор громкости
            elements.volumeSlider.addEventListener('input', (e) => {
                const volume = e.target.value / 100;
                conferenceParticipants.forEach(participant => {
                    if (participant.audioElement) {
                        participant.audioElement.volume = volume;
                    }
                });
            });
            
            // Кнопка копирования ссылки
            elements.copyLinkBtn.addEventListener('click', copyInviteLink);
            
            // Модальные окна
            elements.startConferenceBtn.addEventListener('click', () => {
                elements.createConferenceModal.style.display = 'none';
                joinConferenceAfterCreate();
            });
            
            elements.closeCreateModal.addEventListener('click', () => {
                elements.createConferenceModal.style.display = 'none';
            });
            
            elements.acceptInviteBtn.addEventListener('click', acceptInvite);
            elements.declineInviteBtn.addEventListener('click', () => {
                elements.inviteModal.style.display = 'none';
            });
            
            // Приглашение по нажатию Enter в поле ID
            elements.conferenceId.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    joinConference();
                }
            });
        }
        
        // Создание конференции
        async function createConference() {
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                showNotification('Нет соединения с сервером', 'warning');
                return;
            }
            
            try {
                // Запрашиваем доступ к микрофону
                localStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true,
                        channelCount: 1
                    },
                    video: false
                });
                
                // Отправляем запрос на создание конференции
                ws.send(JSON.stringify({
                    type: 'create_conference',
                    name: userName
                }));
                
                // Обновляем состояние микрофона
                updateMicrophoneStatus(false);
                showNotification('Микрофон активирован', 'success');
                
            } catch (error) {
                console.error('Ошибка доступа к микрофону:', error);
                showNotification('Не удалось получить доступ к микрофону', 'danger');
            }
        }
        
        // Присоединение к конференции
        async function joinConference() {
            const targetConferenceId = elements.conferenceId.value.trim();
            
            if (!targetConferenceId) {
                showNotification('Введите ID конференции', 'warning');
                return;
            }
            
            if (!ws || ws.readyState !== WebSocket.OPEN) {
                showNotification('Нет соединения с сервером', 'warning');
                return;
            }
            
            try {
                // Запрашиваем доступ к микрофону
                if (!localStream) {
                    localStream = await navigator.mediaDevices.getUserMedia({
                        audio: {
                            echoCancellation: true,
                            noiseSuppression: true,
                            autoGainControl: true,
                            channelCount: 1
                        },
                        video: false
                    });
                }
                
                // Отправляем запрос на присоединение
                ws.send(JSON.stringify({
                    type: 'join_conference',
                    conference_id: targetConferenceId,
                    name: userName
                }));
                
                updateConnectionStatus('connecting', 'Подключение...');
                showNotification(`Присоединение к конференции ${targetConferenceId}`, 'info');
                
            } catch (error) {
                console.error('Ошибка доступа к микрофону:', error);
                showNotification('Не удалось получить доступ к микрофону', 'danger');
            }
        }
        
        // Присоединение к созданной конференции
        function joinConferenceAfterCreate() {
            ws.send(JSON.stringify({
                type: 'join_conference',
                conference_id: conferenceId,
                name: userName
            }));
        }
        
        // Выход из конференции
        function leaveConference() {
            if (!isInConference || !conferenceId) return;
            
            // Отправляем уведомление о выходе
            ws.send(JSON.stringify({
                type: 'leave_conference',
                conference_id: conferenceId
            }));
            
            // Закрываем все PeerConnection
            peerConnections.forEach((pc, participantId) => {
                pc.close();
            });
            peerConnections.clear();
            
            // Останавливаем локальный поток
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
                localStream = null;
            }
            
            // Очищаем интерфейс
            conferenceParticipants.clear();
            elements.conferenceGrid.innerHTML = '';
            elements.conferenceGrid.style.display = 'none';
            elements.noConferenceMessage.style.display = 'block';
            elements.inviteSection.style.display = 'none';
            
            // Сбрасываем состояние
            isInConference = false;
            conferenceId = null;
            conferenceStartTime = null;
            
            // Обновляем UI
            elements.leaveConferenceBtn.disabled = true;
            elements.createConferenceBtn.disabled = false;
            elements.joinConferenceBtn.disabled = false;
            elements.conferenceId.disabled = false;
            elements.muteBtn.disabled = true;
            
            // Останавливаем таймер
            if (timerInterval) {
                clearInterval(timerInterval);
                timerInterval = null;
            }
            
            // Обновляем таймеры
            elements.conferenceTimer.textContent = '00:00';
            elements.callTimer.textContent = '--:--';
            
            showNotification('Вы вышли из конференции', 'info');
            updateParticipantsList();
            updateStatusBar();
        }
        
        // Обработчики сообщений WebSocket
        function handleYourId(data) {
            userId = data.user_id;
            elements.userId.textContent = userId;
            console.log(`✅ Ваш ID: ${userId}`);
        }
        
        function handleConferenceCreated(data) {
            conferenceId = data.conference_id;
            elements.generatedConferenceId.textContent = conferenceId;
            
            // Обновляем ссылку приглашения
            const inviteUrl = `${window.location.origin}/?conference=${conferenceId}`;
            elements.modalInviteLink.textContent = inviteUrl;
            elements.inviteLink.textContent = inviteUrl;
            
            // Показываем модальное окно
            elements.createConferenceModal.style.display = 'flex';
            showNotification('Конференция создана!', 'success');
        }
        
        function handleConferenceJoined(data) {
            conferenceId = data.conference_id;
            isInConference = true;
            
            // Обновляем интерфейс
            elements.conferenceGrid.style.display = 'grid';
            elements.noConferenceMessage.style.display = 'none';
            elements.inviteSection.style.display = 'block';
            elements.leaveConferenceBtn.disabled = false;
            elements.createConferenceBtn.disabled = true;
            elements.joinConferenceBtn.disabled = true;
            elements.conferenceId.disabled = true;
            elements.muteBtn.disabled = false;
            
            // Запускаем таймер
            conferenceStartTime = Date.now();
            startConferenceTimer();
            
            // Добавляем себя в список участников
            addParticipant(userId, userName, true);
            
            // Устанавливаем соединения с другими участниками
            if (data.participants) {
                data.participants.forEach(participant => {
                    if (participant.id !== userId) {
                        addParticipant(participant.id, participant.name);
                        createPeerConnection(participant.id);
                    }
                });
            }
            
            updateConnectionStatus('connected', 'В конференции');
            showNotification(`Вы присоединились к конференции ${conferenceId}`, 'success');
        }
        
        function handleParticipantJoined(data) {
            if (data.participant_id !== userId) {
                addParticipant(data.participant_id, data.name || `Участник ${data.participant_id}`);
                createPeerConnection(data.participant_id);
                showNotification(`${data.name || 'Новый участник'} присоединился`, 'info');
            }
        }
        
        function handleParticipantLeft(data) {
            const participantId = data.participant_id;
            if (participantId === userId) return;
            
            // Удаляем участника
            removeParticipant(participantId);
            
            // Закрываем PeerConnection
            if (peerConnections.has(participantId)) {
                peerConnections.get(participantId).close();
                peerConnections.delete(participantId);
            }
            
            showNotification(`${data.name || 'Участник'} вышел`, 'warning');
        }
        
        function handleParticipantUpdated(data) {
            const participant = conferenceParticipants.get(data.participant_id);
            if (participant) {
                participant.name = data.name;
                updateParticipantDisplay(data.participant_id);
            }
        }
        
        function handleConferenceInfo(data) {
            // Обновляем список участников
            conferenceParticipants.clear();
            elements.conferenceGrid.innerHTML = '';
            elements.participantsList.innerHTML = '';
            
            // Добавляем себя
            addParticipant(userId, userName, true);
            
            // Добавляем других участников
            data.participants.forEach(participant => {
                if (participant.id !== userId) {
                    addParticipant(participant.id, participant.name);
                }
            });
            
            // Устанавливаем соединения
            data.participants.forEach(participant => {
                if (participant.id !== userId && !peerConnections.has(participant.id)) {
                    createPeerConnection(participant.id);
                }
            });
            
            updateParticipantsList();
            updateStatusBar();
        }
        
        // WebRTC функции
        function createPeerConnection(participantId) {
            if (peerConnections.has(participantId)) {
                console.log(`PeerConnection с ${participantId} уже существует`);
                return;
            }
            
            console.log(`Создаю PeerConnection для ${participantId}`);
            
            const configuration = {
                iceServers: [
                    { urls: 'stun:stun.l.google.com:19302' },
                    { urls: 'stun:stun1.l.google.com:19302' },
                    { urls: 'stun:stun2.l.google.com:19302' }
                ]
            };
            
            const pc = new RTCPeerConnection(configuration);
            peerConnections.set(participantId, pc);
            
            // Отправляем ICE кандидаты
            pc.onicecandidate = (event) => {
                if (event.candidate && ws && conferenceId) {
                    ws.send(JSON.stringify({
                        type: 'ice_candidate',
                        conference_id: conferenceId,
                        target_id: participantId,
                        candidate: event.candidate
                    }));
                }
            };
            
            // Получаем удаленный поток
            pc.ontrack = (event) => {
                console.log(`Получен поток от ${participantId}`);
                const participant = conferenceParticipants.get(participantId);
                if (participant && event.streams[0]) {
                    participant.stream = event.streams[0];
                    setupAudioElement(participantId, event.streams[0]);
                }
            };
            
            // Отслеживаем состояние соединения
            pc.onconnectionstatechange = () => {
                console.log(`Состояние соединения с ${participantId}: ${pc.connectionState}`);
            };
            
            // Добавляем локальный поток, если он есть
            if (localStream) {
                localStream.getTracks().forEach(track => {
                    pc.addTrack(track, localStream);
                });
            }
            
            // Создаем и отправляем offer
            createOffer(pc, participantId);
        }
        
        async function createOffer(pc, participantId) {
            try {
                const offer = await pc.createOffer({
                    offerToReceiveAudio: true,
                    offerToReceiveVideo: false
                });
                
                await pc.setLocalDescription(offer);
                
                if (ws && conferenceId) {
                    ws.send(JSON.stringify({
                        type: 'offer',
                        conference_id: conferenceId,
                        target_id: participantId,
                        offer: offer
                    }));
                }
            } catch (error) {
                console.error('Ошибка создания offer:', error);
            }
        }
        
        async function handleOffer(data) {
            const participantId = data.sender_id;
            
            if (!peerConnections.has(participantId)) {
                createPeerConnection(participantId);
            }
            
            const pc = peerConnections.get(participantId);
            
            try {
                await pc.setRemoteDescription(new RTCSessionDescription(data.offer));
                const answer = await pc.createAnswer();
                await pc.setLocalDescription(answer);
                
                if (ws && conferenceId) {
                    ws.send(JSON.stringify({
                        type: 'answer',
                        conference_id: conferenceId,
                        target_id: participantId,
                        answer: answer
                    }));
                }
            } catch (error) {
                console.error('Ошибка обработки offer:', error);
            }
        }
        
        async function handleAnswer(data) {
            const participantId = data.sender_id;
            const pc = peerConnections.get(participantId);
            
            if (pc) {
                try {
                    await pc.setRemoteDescription(new RTCSessionDescription(data.answer));
                } catch (error) {
                    console.error('Ошибка установки answer:', error);
                }
            }
        }
        
        async function handleIceCandidate(data) {
            const participantId = data.sender_id;
            const pc = peerConnections.get(participantId);
            
            if (pc && pc.remoteDescription) {
                try {
                    await pc.addIceCandidate(new RTCIceCandidate(data.candidate));
                } catch (error) {
                    console.error('Ошибка добавления ICE кандидата:', error);
                }
            }
        }
        
        // Функции для работы с участниками
        function addParticipant(participantId, name, isLocal = false) {
            const audioElement = document.createElement('audio');
            audioElement.autoplay = true;
            audioElement.volume = elements.volumeSlider.value / 100;
            audioElement.style.display = 'none';
            
            conferenceParticipants.set(participantId, {
                id: participantId,
                name: name,
                audioElement: audioElement,
                stream: null,
                muted: false,
                volume: 1.0,
                isLocal: isLocal
            });
            
            document.body.appendChild(audioElement);
            createParticipantVideoElement(participantId, isLocal);
            updateParticipantsList();
            updateStatusBar();
        }
        
        function removeParticipant(participantId) {
            const participant = conferenceParticipants.get(participantId);
            if (participant) {
                if (participant.audioElement) {
                    participant.audioElement.remove();
                }
                conferenceParticipants.delete(participantId);
                
                // Удаляем видео элемент
                const videoElement = document.getElementById(`video-${participantId}`);
                if (videoElement) {
                    videoElement.remove();
                }
            }
            
            updateParticipantsList();
            updateStatusBar();
        }
        
        function setupAudioElement(participantId, stream) {
            const participant = conferenceParticipants.get(participantId);
            if (!participant || !participant.audioElement) return;
            
            participant.audioElement.srcObject = stream;
            
            // Настраиваем визуализатор аудио
            setupAudioVisualizer(participantId, stream);
        }
        
        function createParticipantVideoElement(participantId, isLocal = false) {
            const participant = conferenceParticipants.get(participantId);
            if (!participant) return;
            
            const videoContainer = document.createElement('div');
            videoContainer.className = `participant-video ${isLocal ? 'self-video' : ''}`;
            videoContainer.id = `video-${participantId}`;
            
            const audioVisualizer = document.createElement('div');
            audioVisualizer.className = 'audio-visualizer';
            audioVisualizer.id = `visualizer-${participantId}`;
            
            // Создаем бары для визуализатора
            for (let i = 0; i < 20; i++) {
                const bar = document.createElement('div');
                bar.className = 'bar';
                bar.style.animationDelay = `${i * 0.05}s`;
                audioVisualizer.appendChild(bar);
            }
            
            const videoInfo = document.createElement('div');
            videoInfo.className = 'video-info';
            
            const nameSpan = document.createElement('span');
            nameSpan.className = 'video-name';
            nameSpan.textContent = participant.name;
            
            const controlsDiv = document.createElement('div');
            controlsDiv.className = 'video-controls';
            
            const volumeBtn = document.createElement('button');
            volumeBtn.className = 'control-btn';
            volumeBtn.innerHTML = '<i class="fas fa-volume-up"></i>';
            volumeBtn.title = 'Настроить громкость';
            volumeBtn.onclick = () => adjustParticipantVolume(participantId);
            
            const muteBtn = document.createElement('button');
            muteBtn.className = 'control-btn';
            muteBtn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
            muteBtn.title = 'Заглушить участника';
            muteBtn.onclick = () => toggleParticipantMute(participantId);
            
            controlsDiv.appendChild(volumeBtn);
            controlsDiv.appendChild(muteBtn);
            
            videoInfo.appendChild(nameSpan);
            videoInfo.appendChild(controlsDiv);
            
            videoContainer.appendChild(audioVisualizer);
            videoContainer.appendChild(videoInfo);
            
            if (isLocal) {
                const selfLabel = document.createElement('div');
                selfLabel.className = 'self-label';
                selfLabel.innerHTML = '<i class="fas fa-user"></i> Вы';
                videoContainer.appendChild(selfLabel);
            }
            
            elements.conferenceGrid.appendChild(videoContainer);
        }
        
        function updateParticipantDisplay(participantId) {
            const participant = conferenceParticipants.get(participantId);
            if (!participant) return;
            
            const videoElement = document.getElementById(`video-${participantId}`);
            if (videoElement) {
                const nameSpan = videoElement.querySelector('.video-name');
                if (nameSpan) {
                    nameSpan.textContent = participant.name;
                }
            }
            
            updateParticipantsList();
        }
        
        function updateLocalParticipantDisplay() {
            const participant = conferenceParticipants.get(userId);
            if (participant) {
                participant.name = userName;
                updateParticipantDisplay(userId);
            }
        }
        
        // Визуализатор аудио
        function setupAudioVisualizer(participantId, stream) {
            if (!audioContext) {
                audioContext = new (window.AudioContext || window.webkitAudioContext)();
            }
            
            const source = audioContext.createMediaStreamSource(stream);
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 256;
            analyser.smoothingTimeConstant = 0.8;
            
            source.connect(analyser);
            analysers.set(participantId, analyser);
            
            // Запускаем анимацию визуализатора
            animateVisualizer(participantId);
        }
        
        function animateVisualizer(participantId) {
            const analyser = analysers.get(participantId);
            const visualizer = document.getElementById(`visualizer-${participantId}`);
            
            if (!analyser || !visualizer) return;
            
            const bufferLength = analyser.frequencyBinCount;
            const dataArray = new Uint8Array(bufferLength);
            
            function draw() {
                if (!analysers.has(participantId)) return;
                
                analyser.getByteFrequencyData(dataArray);
                const bars = visualizer.querySelectorAll('.bar');
                
                let sum = 0;
                for (let i = 0; i < bars.length; i++) {
                    const value = dataArray[Math.floor(i * bufferLength / bars.length)];
                    const height = Math.max(5, value / 2);
                    bars[i].style.height = `${height}px`;
                    bars[i].style.opacity = Math.max(0.3, value / 255);
                    sum += value;
                }
                
                // Определяем активного говорящего
                const average = sum / bufferLength;
                if (average > 20 && participantId !== activeSpeaker) {
                    setActiveSpeaker(participantId);
                }
                
                requestAnimationFrame(draw);
            }
            
            draw();
        }
        
        function setActiveSpeaker(participantId) {
            // Убираем подсветку у предыдущего активного говорящего
            if (activeSpeaker) {
                const prevVideo = document.getElementById(`video-${activeSpeaker}`);
                if (prevVideo) {
                    prevVideo.classList.remove('active-speaker');
                }
            }
            
            // Подсвечиваем нового активного говорящего
            activeSpeaker = participantId;
            const video = document.getElementById(`video-${participantId}`);
            if (video) {
                video.classList.add('active-speaker');
            }
            
            // Сбрасываем через 2 секунды
            setTimeout(() => {
                if (activeSpeaker === participantId) {
                    activeSpeaker = null;
                    if (video) {
                        video.classList.remove('active-speaker');
                    }
                }
            }, 2000);
        }
        
        // Управление микрофоном
        async function toggleMicrophone() {
            if (!localStream) return;
            
            const audioTrack = localStream.getAudioTracks()[0];
            if (audioTrack) {
                isMuted = !isMuted;
                audioTrack.enabled = !isMuted;
                
                // Обновляем кнопку
                if (isMuted) {
                    elements.muteBtn.innerHTML = '<i class="fas fa-microphone-slash"></i> Включить микрофон';
                    elements.muteBtn.classList.remove('btn-warning');
                    elements.muteBtn.classList.add('btn-success');
                } else {
                    elements.muteBtn.innerHTML = '<i class="fas fa-microphone"></i> Выключить микрофон';
                    elements.muteBtn.classList.remove('btn-success');
                    elements.muteBtn.classList.add('btn-warning');
                }
                
                updateMicrophoneStatus(isMuted);
                showNotification(`Микрофон ${isMuted ? 'выключен' : 'включен'}`, 'info');
                
                // Отправляем обновление состояния
                if (ws && conferenceId) {
                    ws.send(JSON.stringify({
                        type: 'update_participant',
                        conference_id: conferenceId,
                        muted: isMuted
                    }));
                }
            }
        }
        
        function toggleParticipantMute(participantId) {
            const participant = conferenceParticipants.get(participantId);
            if (participant && participant.audioElement) {
                participant.muted = !participant.muted;
                participant.audioElement.muted = participant.muted;
                
                // Обновляем отображение
                const videoElement = document.getElementById(`video-${participantId}`);
                if (videoElement) {
                    const muteIcon = videoElement.querySelector('.fa-microphone-slash');
                    if (muteIcon) {
                        muteIcon.style.color = participant.muted ? '#ff416c' : 'white';
                    }
                }
                
                showNotification(`${participant.name} ${participant.muted ? 'заглушен' : 'разблокирован'}`, 'info');
            }
        }
        
        function adjustParticipantVolume(participantId) {
            const participant = conferenceParticipants.get(participantId);
            if (participant && participant.audioElement) {
                const newVolume = prompt(`Громкость для ${participant.name} (0-100):`, Math.round(participant.audioElement.volume * 100));
                if (newVolume !== null) {
                    const volume = Math.min(100, Math.max(0, parseInt(newVolume) || 100)) / 100;
                    participant.audioElement.volume = volume;
                    participant.volume = volume;
                    showNotification(`Громкость ${participant.name} установлена на ${Math.round(volume * 100)}%`, 'success');
                }
            }
        }
        
        // Приглашения
        function handleInvite(data) {
            elements.inviterName.textContent = data.inviter_name || 'Пользователь';
            elements.inviteConferenceId.textContent = `ID: ${data.conference_id}`;
            elements.inviteModal.style.display = 'flex';
            
            // Автоматически скрываем через 30 секунд
            setTimeout(() => {
                if (elements.inviteModal.style.display === 'flex') {
                    elements.inviteModal.style.display = 'none';
                }
            }, 30000);
        }
        
        function acceptInvite() {
            elements.inviteModal.style.display = 'none';
            const conferenceIdFromInvite = elements.inviteConferenceId.textContent.replace('ID: ', '');
            elements.conferenceId.value = conferenceIdFromInvite;
            joinConference();
        }
        
        // Обновление UI
        function updateParticipantsList() {
            elements.participantsList.innerHTML = '';
            let localParticipantAdded = false;
            
            conferenceParticipants.forEach((participant, id) => {
                if (participant.isLocal) {
                    localParticipantAdded = true;
                }
                
                const participantItem = document.createElement('div');
                participantItem.className = 'participant-item';
                
                const participantInfo = document.createElement('div');
                participantInfo.className = 'participant-info';
                
                const avatar = document.createElement('div');
                avatar.className = 'participant-avatar';
                avatar.textContent = participant.name.charAt(0).toUpperCase();
                
                const textDiv = document.createElement('div');
                
                const nameSpan = document.createElement('div');
                nameSpan.className = 'participant-name';
                nameSpan.textContent = participant.name;
                
                const statusSpan = document.createElement('div');
                statusSpan.className = 'participant-status';
                statusSpan.textContent = participant.isLocal ? 'Вы' : (participant.muted ? 'Заглушен' : 'В сети');
                
                textDiv.appendChild(nameSpan);
                textDiv.appendChild(statusSpan);
                
                participantInfo.appendChild(avatar);
                participantInfo.appendChild(textDiv);
                
                participantItem.appendChild(participantInfo);
                
                if (!participant.isLocal) {
                    const muteIcon = document.createElement('div');
                    muteIcon.className = 'participant-muted';
                    muteIcon.innerHTML = participant.muted ? '<i class="fas fa-microphone-slash"></i>' : '<i class="fas fa-microphone"></i>';
                    participantItem.appendChild(muteIcon);
                }
                
                elements.participantsList.appendChild(participantItem);
            });
            
            // Добавляем себя, если еще не добавлены
            if (!localParticipantAdded && userId) {
                const participantItem = document.createElement('div');
                participantItem.className = 'participant-item';
                
                const participantInfo = document.createElement('div');
                participantInfo.className = 'participant-info';
                
                const avatar = document.createElement('div');
                avatar.className = 'participant-avatar';
                avatar.textContent = userName.charAt(0).toUpperCase();
                
                const textDiv = document.createElement('div');
                
                const nameSpan = document.createElement('div');
                nameSpan.className = 'participant-name';
                nameSpan.textContent = `${userName} (Вы)`;
                
                const statusSpan = document.createElement('div');
                statusSpan.className = 'participant-status';
                statusSpan.textContent = isMuted ? 'Микрофон выключен' : 'В сети';
                
                textDiv.appendChild(nameSpan);
                textDiv.appendChild(statusSpan);
                
                participantInfo.appendChild(avatar);
                participantInfo.appendChild(textDiv);
                participantItem.appendChild(participantInfo);
                elements.participantsList.appendChild(participantItem);
            }
            
            elements.participantsCount.textContent = conferenceParticipants.size;
        }
        
        function updateStatusBar() {
            elements.onlineCount.textContent = conferenceParticipants.size;
            elements.micStatus.textContent = isMuted ? 'Выкл' : 'Вкл';
        }
        
        function updateConnectionStatus(status, text) {
            elements.connectionStatus.className = 'status-indicator';
            elements.connectionStatus.classList.add(`status-${status}`);
            elements.connectionText.textContent = text;
        }
        
        function updateMicrophoneStatus(muted) {
            elements.micStatus.textContent = muted ? 'Выкл' : 'Вкл';
        }
        
        // Таймер конференции
        function startConferenceTimer() {
            if (timerInterval) {
                clearInterval(timerInterval);
            }
            
            timerInterval = setInterval(() => {
                if (conferenceStartTime) {
                    const elapsed = Date.now() - conferenceStartTime;
                    const minutes = Math.floor(elapsed / 60000);
                    const seconds = Math.floor((elapsed % 60000) / 1000);
                    
                    const timeString = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
                    elements.conferenceTimer.textContent = timeString;
                    elements.callTimer.textContent = timeString;
                }
            }, 1000);
        }
        
        // Уведомления
        function showNotification(message, type = 'info') {
            elements.notificationMessage.textContent = message;
            elements.notification.className = 'notification';
            elements.notification.classList.add(`notification-${type}`);
            elements.notification.classList.add('show');
            
            // Скрываем через 3 секунды
            setTimeout(() => {
                elements.notification.classList.remove('show');
            }, 3000);
        }
        
        // Обработка ошибок
        function handleError(data) {
            showNotification(data.message, 'danger');
            console.error('Ошибка сервера:', data.message);
        }
        
        // Вспомогательные функции
        function copyInviteLink() {
            const link = elements.inviteLink.textContent;
            navigator.clipboard.writeText(link)
                .then(() => {
                    showNotification('Ссылка скопирована в буфер обмена', 'success');
                })
                .catch(err => {
                    console.error('Ошибка копирования:', err);
                    showNotification('Не удалось скопировать ссылку', 'danger');
                });
        }
        
        // Загрузка параметров из URL
        function loadUrlParams() {
            const urlParams = new URLSearchParams(window.location.search);
            const conferenceParam = urlParams.get('conference');
            
            if (conferenceParam) {
                elements.conferenceId.value = conferenceParam;
                showNotification(`Обнаружена ссылка на конференцию. Нажмите "Присоединиться" для подключения.`, 'info');
            }
        }
        
        // Инициализация при загрузке страницы
        window.addEventListener('load', () => {
            init();
            loadUrlParams();
        });
        
        // Предупреждение при закрытии страницы
        window.addEventListener('beforeunload', (e) => {
            if (isInConference) {
                e.preventDefault();
                e.returnValue = 'У вас активная конференция. Вы уверены, что хотите закрыть страницу?';
                return e.returnValue;
            }
        });
    </script>
</body>
</html>"""

# ========== Серверная логика для конференц-связи ==========

# Хранилище данных
conferences = {}  # conference_id -> {creator_id, participants, created_at}
participants = {}  # participant_id -> {conference_id, name, ws, muted}
connected_clients = {}  # participant_id -> ws

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
            name="Конференц-связь",
            auth=Auth.NONE
        )
        
        public_url = endpoint.url
        print(f"✅ Сервис опубликован!")
        print(f"🌐 Публичный URL: {public_url}")
        print("=" * 50)
        
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

async def http_handler(request):
    """Отдаем HTML страницу"""
    return web.Response(text=HTML_PAGE, content_type='text/html')

async def websocket_handler(request):
    """Обрабатываем WebSocket соединения для конференц-связи"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    client_id = str(uuid.uuid4())[:8]
    connected_clients[client_id] = ws
    
    print(f"👤 {client_id} подключился")
    
    try:
        # Отправляем клиенту его ID
        await ws.send_json({
            "type": "your_id",
            "user_id": client_id
        })
        
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    data["sender_id"] = client_id
                    
                    await handle_websocket_message(data, ws)
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Ошибка JSON у {client_id}: {e}")
                    await ws.send_json({
                        "type": "error",
                        "message": "Некорректный формат данных"
                    })
                except Exception as e:
                    print(f"❌ Ошибка обработки сообщения у {client_id}: {e}")
                    
    except Exception as e:
        print(f"❌ Ошибка WebSocket у {client_id}: {e}")
    finally:
        await handle_client_disconnect(client_id)
        print(f"👋 {client_id} отключился")
        
    return ws

async def handle_websocket_message(data, ws):
    """Обрабатываем сообщения от клиента"""
    client_id = data["sender_id"]
    msg_type = data.get("type")
    
    if msg_type == "create_conference":
        await create_conference(data, client_id, ws)
        
    elif msg_type == "join_conference":
        await join_conference(data, client_id, ws)
        
    elif msg_type == "leave_conference":
        await leave_conference(data, client_id)
        
    elif msg_type == "update_participant":
        await update_participant(data, client_id)
        
    elif msg_type == "invite_to_conference":
        await invite_to_conference(data, client_id)
        
    elif msg_type == "offer":
        await forward_offer(data, client_id)
        
    elif msg_type == "answer":
        await forward_answer(data, client_id)
        
    elif msg_type == "ice_candidate":
        await forward_ice_candidate(data, client_id)

async def create_conference(data, client_id, ws):
    """Создание новой конференции"""
    conference_id = str(uuid.uuid4())[:8]
    user_name = data.get("name", "Участник")
    
    conferences[conference_id] = {
        "creator_id": client_id,
        "participants": {},
        "created_at": datetime.now().isoformat()
    }
    
    # Добавляем создателя в участники
    participants[client_id] = {
        "conference_id": conference_id,
        "name": user_name,
        "ws": ws,
        "muted": False
    }
    
    conferences[conference_id]["participants"][client_id] = {
        "id": client_id,
        "name": user_name,
        "muted": False
    }
    
    # Отправляем ID конференции создателю
    await ws.send_json({
        "type": "conference_created",
        "conference_id": conference_id
    })
    
    print(f"📞 Конференция {conference_id} создана пользователем {client_id}")

async def join_conference(data, client_id, ws):
    """Присоединение к существующей конференции"""
    conference_id = data.get("conference_id")
    user_name = data.get("name", "Участник")
    
    if conference_id not in conferences:
        await ws.send_json({
            "type": "error",
            "message": "Конференция не найдена"
        })
        return
    
    conference = conferences[conference_id]
    
    # Проверяем максимальное количество участников
    if len(conference["participants"]) >= 10:
        await ws.send_json({
            "type": "error",
            "message": "Конференция заполнена (максимум 10 участников)"
        })
        return
    
    # Добавляем участника
    participants[client_id] = {
        "conference_id": conference_id,
        "name": user_name,
        "ws": ws,
        "muted": False
    }
    
    conference["participants"][client_id] = {
        "id": client_id,
        "name": user_name,
        "muted": False
    }
    
    # Уведомляем нового участника о присоединении
    await ws.send_json({
        "type": "conference_joined",
        "conference_id": conference_id,
        "participants": list(conference["participants"].values())
    })
    
    # Уведомляем всех остальных участников о новом участнике
    for participant_id, participant_data in conference["participants"].items():
        if participant_id != client_id and participant_id in connected_clients:
            try:
                await connected_clients[participant_id].send_json({
                    "type": "participant_joined",
                    "participant_id": client_id,
                    "name": user_name
                })
            except:
                pass
    
    print(f"👥 {client_id} присоединился к конференции {conference_id}")

async def leave_conference(data, client_id):
    """Выход из конференции"""
    if client_id not in participants:
        return
    
    conference_id = participants[client_id]["conference_id"]
    user_name = participants[client_id]["name"]
    
    if conference_id in conferences:
        conference = conferences[conference_id]
        
        # Удаляем участника из конференции
        if client_id in conference["participants"]:
            del conference["participants"][client_id]
        
        # Удаляем участника из общего списка
        if client_id in participants:
            del participants[client_id]
        
        # Уведомляем остальных участников
        for participant_id, participant_data in conference["participants"].items():
            if participant_id in connected_clients:
                try:
                    await connected_clients[participant_id].send_json({
                        "type": "participant_left",
                        "participant_id": client_id,
                        "name": user_name
                    })
                except:
                    pass
        
        # Если конференция пуста, удаляем её
        if not conference["participants"]:
            del conferences[conference_id]
            print(f"🗑️ Конференция {conference_id} удалена (нет участников)")
        else:
            print(f"👋 {client_id} вышел из конференции {conference_id}")

async def update_participant(data, client_id):
    """Обновление данных участника (имя, состояние микрофона)"""
    if client_id not in participants:
        return
    
    conference_id = participants[client_id]["conference_id"]
    
    if conference_id in conferences:
        conference = conferences[conference_id]
        
        # Обновляем имя
        if "name" in data:
            participants[client_id]["name"] = data["name"]
            if client_id in conference["participants"]:
                conference["participants"][client_id]["name"] = data["name"]
        
        # Обновляем состояние микрофона
        if "muted" in data:
            participants[client_id]["muted"] = data["muted"]
            if client_id in conference["participants"]:
                conference["participants"][client_id]["muted"] = data["muted"]
        
        # Уведомляем других участников об изменениях
        for participant_id, participant_data in conference["participants"].items():
            if participant_id != client_id and participant_id in connected_clients:
                try:
                    await connected_clients[participant_id].send_json({
                        "type": "participant_updated",
                        "participant_id": client_id,
                        "name": participants[client_id]["name"],
                        "muted": participants[client_id]["muted"]
                    })
                except:
                    pass

async def invite_to_conference(data, client_id):
    """Отправка приглашения в конференцию"""
    target_id = data.get("target_id")
    
    if client_id not in participants:
        return
    
    if target_id in connected_clients:
        try:
            await connected_clients[target_id].send_json({
                "type": "invite_to_conference",
                "conference_id": participants[client_id]["conference_id"],
                "inviter_name": participants[client_id]["name"],
                "inviter_id": client_id
            })
            print(f"📨 {client_id} пригласил {target_id} в конференцию")
        except:
            pass

async def forward_offer(data, client_id):
    """Пересылка предложения WebRTC другому участнику"""
    target_id = data.get("target_id")
    conference_id = data.get("conference_id")
    
    # Проверяем, что оба участника в одной конференции
    if (client_id in participants and target_id in participants and
        participants[client_id]["conference_id"] == participants[target_id]["conference_id"] == conference_id):
        
        if target_id in connected_clients:
            try:
                await connected_clients[target_id].send_json({
                    "type": "offer",
                    "sender_id": client_id,
                    "offer": data["offer"]
                })
            except:
                pass

async def forward_answer(data, client_id):
    """Пересылка ответа WebRTC другому участнику"""
    target_id = data.get("target_id")
    conference_id = data.get("conference_id")
    
    if (client_id in participants and target_id in participants and
        participants[client_id]["conference_id"] == participants[target_id]["conference_id"] == conference_id):
        
        if target_id in connected_clients:
            try:
                await connected_clients[target_id].send_json({
                    "type": "answer",
                    "sender_id": client_id,
                    "answer": data["answer"]
                })
            except:
                pass

async def forward_ice_candidate(data, client_id):
    """Пересылка ICE кандидата WebRTC"""
    target_id = data.get("target_id")
    conference_id = data.get("conference_id")
    
    if (client_id in participants and target_id in participants and
        participants[client_id]["conference_id"] == participants[target_id]["conference_id"] == conference_id):
        
        if target_id in connected_clients:
            try:
                await connected_clients[target_id].send_json({
                    "type": "ice_candidate",
                    "sender_id": client_id,
                    "candidate": data["candidate"]
                })
            except:
                pass

async def handle_client_disconnect(client_id):
    """Обработка отключения клиента"""
    if client_id in connected_clients:
        del connected_clients[client_id]
    
    if client_id in participants:
        conference_id = participants[client_id]["conference_id"]
        user_name = participants[client_id]["name"]
        
        if conference_id in conferences:
            conference = conferences[conference_id]
            
            # Удаляем участника из конференции
            if client_id in conference["participants"]:
                del conference["participants"][client_id]
            
            # Удаляем участника из общего списка
            del participants[client_id]
            
            # Уведомляем остальных участников
            for participant_id, participant_data in conference["participants"].items():
                if participant_id in connected_clients:
                    try:
                        await connected_clients[participant_id].send_json({
                            "type": "participant_left",
                            "participant_id": client_id,
                            "name": user_name
                        })
                    except:
                        pass
            
            # Если конференция пуста, удаляем её
            if not conference["participants"]:
                del conferences[conference_id]
                print(f"🗑️ Конференция {conference_id} удалена (нет участников)")

async def main():
    """Запускаем сервер конференц-связи"""
    print("=" * 60)
    print("🎙️  КОНФЕРЕНЦ-СВЯЗЬ С CLOUDPUB")
    print("=" * 60)
    
    app = web.Application()
    app.router.add_get('/', http_handler)
    app.router.add_get('/ws', websocket_handler)
    
    # Настраиваем CORS
    async def cors_middleware(app, handler):
        async def middleware_handler(request):
            response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST'
            return response
        return middleware_handler
    
    app.middlewares.append(cors_middleware)
    
    # Запускаем сервер
    runner = web.AppRunner(app)
    await runner.setup()
    
    LOCAL_PORT = 8080
    site = web.TCPSite(runner, '0.0.0.0', LOCAL_PORT)
    await site.start()
    
    print(f"✅ СЕРВЕР КОНФЕРЕНЦ-СВЯЗИ ЗАПУЩЕН!")
    print(f"🌐 Локальный URL: http://localhost:{LOCAL_PORT}")
    print("=" * 60)
    print("🎯 Возможности:")
    print("   • Групповые звонки до 10 участников")
    print("   • Визуализация активности говорящих")
    print("   • Индивидуальная настройка громкости")
    print("   • Приглашения по ссылке")
    print("   • Управление микрофоном")
    print("=" * 60)
    
    # Публикуем через CloudPub
    if CLOUDPUB_AVAILABLE:
        await publish_with_cloudpub(LOCAL_PORT)
    else:
        print("⚠️  CloudPub не установлен. Установите: pip install cloudpub-python-sdk")
        print("   Конференция будет работать только в локальной сети")
        print("=" * 60)
        print("📱 Для телефона в той же Wi-Fi:")
        print("   http://ваш-IP-адрес:8080")
        print("=" * 60)
    
    # Периодически очищаем неактивные конференции
    async def cleanup_task():
        while True:
            await asyncio.sleep(300)  # Каждые 5 минут
            await cleanup_inactive_conferences()
    
    asyncio.create_task(cleanup_task())
    
    # Ждем вечно
    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        print("\n🛑 Останавливаю сервер...")
        await cleanup_before_shutdown()

async def cleanup_inactive_conferences():
    """Очистка неактивных конференций"""
    now = datetime.now()
    conferences_to_remove = []
    
    for conference_id, conference_data in conferences.items():
        created_at = datetime.fromisoformat(conference_data["created_at"])
        time_diff = (now - created_at).total_seconds()
        
        # Удаляем конференции старше 2 часов без участников
        if time_diff > 7200 and not conference_data["participants"]:
            conferences_to_remove.append(conference_id)
    
    for conference_id in conferences_to_remove:
        del conferences[conference_id]
        print(f"🗑️ Удалена неактивная конференция {conference_id}")

async def cleanup_before_shutdown():
    """Очистка перед завершением работы"""
    # Отменяем публикацию CloudPub
    if cloudpub_info:
        try:
            print("🗑️  Удаляю публикацию CloudPub...")
            cloudpub_info['connection'].unpublish(cloudpub_info['endpoint'].guid)
            print("✅ Публикация удалена")
        except Exception as e:
            print(f"⚠️  Ошибка удаления публикации: {e}")
    
    # Уведомляем всех участников о завершении работы
    for client_id, ws in connected_clients.items():
        try:
            await ws.send_json({
                "type": "error",
                "message": "Сервер останавливается"
            })
            await ws.close()
        except:
            pass

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
        