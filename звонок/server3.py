import asyncio
import json
import random
import time
from datetime import datetime
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

# ========== Хранилище данных ==========
users = {}
messages = []
connected_clients = {}

# ========== HTML страница ==========
HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>GrinMain - Бесплатные звонки и чат</title>
    <style>
    :root {
        --primary-green: #2ecc71;
        --dark-green: #27ae60;
        --light-green: #d5f4e6;
        --white: #ffffff;
        --light-gray: #f5f5f5;
        --gray: #95a5a6;
        --dark-gray: #34495e;
    }
    
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(135deg, #f8fff9 0%, #e8f5e9 100%);
        color: #2c3e50;
        min-height: 100vh;
    }
    
    .container {
        max-width: 1400px;
        margin: 0 auto;
        padding: 20px;
        display: grid;
        grid-template-columns: 350px 1fr 350px;
        gap: 20px;
        height: 97vh;
    }
    
    /* ЛЕВАЯ КОЛОНКА - КОНТАКТЫ */
    .sidebar-left {
        background: var(--white);
        border-radius: 20px;
        box-shadow: 0 5px 25px rgba(46, 204, 113, 0.1);
        display: flex;
        flex-direction: column;
        overflow: hidden;
        border: 2px solid var(--light-green);
    }
    
    .user-profile {
        padding: 25px;
        background: linear-gradient(135deg, var(--primary-green), var(--dark-green));
        color: white;
        display: flex;
        align-items: center;
        gap: 15px;
    }
    
    .user-avatar {
        width: 60px;
        height: 60px;
        border-radius: 50%;
        background: rgba(255,255,255,0.2);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        font-weight: bold;
        border: 3px solid white;
    }
    
    .user-info {
        flex: 1;
    }
    
    .user-name {
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 5px;
    }
    
    .user-id {
        font-size: 14px;
        opacity: 0.9;
        background: rgba(255,255,255,0.2);
        padding: 3px 10px;
        border-radius: 12px;
        display: inline-block;
        font-family: monospace;
        cursor: pointer;
        transition: background 0.3s;
    }
    
    .user-id:hover {
        background: rgba(255,255,255,0.3);
    }
    
    .contacts-header {
        padding: 20px 25px 15px;
        border-bottom: 2px solid var(--light-green);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .contacts-header h2 {
        color: var(--dark-gray);
        font-size: 18px;
    }
    
    .add-contact-btn {
        background: var(--primary-green);
        color: white;
        border: none;
        width: 40px;
        height: 40px;
        border-radius: 50%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        transition: transform 0.3s, background 0.3s;
    }
    
    .add-contact-btn:hover {
        background: var(--dark-green);
        transform: scale(1.1);
    }
    
    .contacts-list {
        flex: 1;
        overflow-y: auto;
        padding: 10px;
    }
    
    .contact-item {
        padding: 15px;
        margin-bottom: 10px;
        background: var(--light-gray);
        border-radius: 15px;
        cursor: pointer;
        transition: all 0.3s;
        border: 2px solid transparent;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    
    .contact-item:hover {
        background: var(--light-green);
        transform: translateX(5px);
    }
    
    .contact-item.active {
        background: var(--white);
        border-color: var(--primary-green);
        box-shadow: 0 5px 15px rgba(46, 204, 113, 0.2);
    }
    
    .contact-avatar {
        width: 45px;
        height: 45px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--primary-green), var(--dark-green));
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-weight: bold;
        font-size: 16px;
    }
    
    .contact-details {
        flex: 1;
    }
    
    .contact-name {
        font-weight: 600;
        color: var(--dark-gray);
        margin-bottom: 3px;
    }
    
    .contact-status {
        font-size: 12px;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: var(--gray);
    }
    
    .status-dot.online {
        background: var(--primary-green);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    
    .contact-actions {
        display: flex;
        gap: 5px;
    }
    
    .action-btn {
        width: 36px;
        height: 36px;
        border-radius: 50%;
        border: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 16px;
        transition: all 0.3s;
    }
    
    .call-btn {
        background: var(--primary-green);
        color: white;
    }
    
    .call-btn:hover {
        background: var(--dark-green);
        transform: scale(1.1);
    }
    
    .message-btn {
        background: #3498db;
        color: white;
    }
    
    .message-btn:hover {
        background: #2980b9;
        transform: scale(1.1);
    }
    
    /* ЦЕНТРАЛЬНАЯ КОЛОНКА - ЧАТ */
    .chat-container {
        background: var(--white);
        border-radius: 20px;
        box-shadow: 0 5px 25px rgba(46, 204, 113, 0.1);
        display: flex;
        flex-direction: column;
        overflow: hidden;
        border: 2px solid var(--light-green);
    }
    
    .chat-header {
        padding: 20px 25px;
        border-bottom: 2px solid var(--light-green);
        background: linear-gradient(to right, rgba(46, 204, 113, 0.05), transparent);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .chat-info h3 {
        color: var(--dark-gray);
        font-size: 20px;
        margin-bottom: 5px;
    }
    
    .chat-status {
        color: var(--gray);
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 5px;
    }
    
    .chat-actions {
        display: flex;
        gap: 10px;
    }
    
    .chat-messages {
        flex: 1;
        padding: 25px;
        overflow-y: auto;
        background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%232ecc71' fill-opacity='0.03'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
    }
    
    .message {
        margin-bottom: 20px;
        max-width: 75%;
        animation: fadeIn 0.3s ease-out;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .message.incoming {
        margin-right: auto;
    }
    
    .message.outgoing {
        margin-left: auto;
    }
    
    .message-bubble {
        padding: 15px 20px;
        border-radius: 20px;
        position: relative;
        box-shadow: 0 3px 10px rgba(0,0,0,0.08);
    }
    
    .message.incoming .message-bubble {
        background: var(--light-green);
        border-bottom-left-radius: 5px;
    }
    
    .message.outgoing .message-bubble {
        background: var(--primary-green);
        color: white;
        border-bottom-right-radius: 5px;
    }
    
    .message-sender {
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 5px;
        color: var(--dark-gray);
    }
    
    .message-time {
        font-size: 12px;
        opacity: 0.7;
        text-align: right;
        margin-top: 5px;
    }
    
    .typing-indicator {
        display: flex;
        gap: 5px;
        padding: 10px 20px;
        background: var(--light-gray);
        border-radius: 20px;
        width: fit-content;
        margin: 10px 0;
    }
    
    .typing-indicator span {
        width: 8px;
        height: 8px;
        background: var(--primary-green);
        border-radius: 50%;
        animation: typing 1.4s infinite ease-in-out;
    }
    
    .typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
    .typing-indicator span:nth-child(2) { animation-delay: -0.16s; }
    
    @keyframes typing {
        0%, 80%, 100% { transform: scale(0); }
        40% { transform: scale(1); }
    }
    
    .message-input-area {
        padding: 20px 25px;
        border-top: 2px solid var(--light-green);
        background: rgba(46, 204, 113, 0.03);
        display: flex;
        gap: 15px;
        align-items: center;
    }
    
    .message-input {
        flex: 1;
        padding: 15px 20px;
        border: 2px solid var(--light-green);
        border-radius: 15px;
        font-size: 16px;
        outline: none;
        transition: border-color 0.3s;
        background: var(--white);
    }
    
    .message-input:focus {
        border-color: var(--primary-green);
        box-shadow: 0 0 0 3px rgba(46, 204, 113, 0.1);
    }
    
    .send-btn {
        background: var(--primary-green);
        color: white;
        border: none;
        width: 55px;
        height: 55px;
        border-radius: 50%;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        transition: all 0.3s;
        box-shadow: 0 5px 15px rgba(46, 204, 113, 0.3);
    }
    
    .send-btn:hover {
        background: var(--dark-green);
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(46, 204, 113, 0.4);
    }
    
    /* ПРАВАЯ КОЛОНКА - ЗВОНКИ */
    .sidebar-right {
        background: var(--white);
        border-radius: 20px;
        box-shadow: 0 5px 25px rgba(46, 204, 113, 0.1);
        display: flex;
        flex-direction: column;
        overflow: hidden;
        border: 2px solid var(--light-green);
    }
    
    .call-header {
        padding: 25px;
        text-align: center;
        background: linear-gradient(to bottom, rgba(46, 204, 113, 0.05), transparent);
    }
    
    .call-header h2 {
        color: var(--dark-gray);
        margin-bottom: 10px;
        font-size: 20px;
    }
    
    .call-controls {
        flex: 1;
        padding: 30px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 25px;
    }
    
    .call-btn-large {
        width: 100px;
        height: 100px;
        border-radius: 50%;
        border: none;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 32px;
        transition: all 0.3s;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
    }
    
    .call-btn-large.call-start {
        background: var(--primary-green);
        color: white;
    }
    
    .call-btn-large.call-start:hover:not(:disabled) {
        background: var(--dark-green);
        transform: scale(1.1);
        box-shadow: 0 15px 40px rgba(46, 204, 113, 0.4);
    }
    
    .call-btn-large.call-end {
        background: #e74c3c;
        color: white;
    }
    
    .call-btn-large.call-end:hover {
        background: #c0392b;
        transform: scale(1.1);
    }
    
    .call-btn-large:disabled {
        opacity: 0.5;
        cursor: not-allowed;
        transform: none !important;
    }
    
    .call-status {
        text-align: center;
        padding: 15px;
        background: var(--light-gray);
        border-radius: 15px;
        width: 100%;
        font-size: 16px;
        color: var(--dark-gray);
        min-height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .call-status.ringing {
        animation: statusPulse 2s infinite;
        background: rgba(46, 204, 113, 0.1);
        color: var(--primary-green);
        font-weight: 600;
    }
    
    @keyframes statusPulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }
    
    .call-audio {
        width: 100%;
        margin-top: 20px;
    }
    
    .empty-state {
        text-align: center;
        padding: 40px 20px;
        color: var(--gray);
    }
    
    .empty-state i {
        font-size: 48px;
        margin-bottom: 15px;
        opacity: 0.5;
    }
    
    /* МОДАЛЬНЫЕ ОКНА */
    .modal {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: rgba(0,0,0,0.5);
        backdrop-filter: blur(5px);
        display: none;
        align-items: center;
        justify-content: center;
        z-index: 1000;
        animation: fadeIn 0.3s ease-out;
    }
    
    .modal-content {
        background: var(--white);
        border-radius: 20px;
        padding: 40px;
        width: 90%;
        max-width: 450px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        border: 2px solid var(--light-green);
        animation: slideUp 0.4s ease-out;
    }
    
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .modal-header {
        margin-bottom: 25px;
        text-align: center;
    }
    
    .modal-header h2 {
        color: var(--dark-gray);
        font-size: 24px;
        margin-bottom: 10px;
    }
    
    .modal-header p {
        color: var(--gray);
        font-size: 16px;
    }
    
    .form-group {
        margin-bottom: 20px;
    }
    
    .form-group label {
        display: block;
        margin-bottom: 8px;
        color: var(--dark-gray);
        font-weight: 500;
    }
    
    .form-control {
        width: 100%;
        padding: 15px 20px;
        border: 2px solid var(--light-green);
        border-radius: 12px;
        font-size: 16px;
        transition: all 0.3s;
        background: var(--white);
    }
    
    .form-control:focus {
        border-color: var(--primary-green);
        box-shadow: 0 0 0 3px rgba(46, 204, 113, 0.1);
        outline: none;
    }
    
    .modal-buttons {
        display: flex;
        gap: 15px;
        margin-top: 30px;
    }
    
    .btn {
        flex: 1;
        padding: 15px 30px;
        border: none;
        border-radius: 12px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s;
        text-align: center;
    }
    
    .btn-primary {
        background: var(--primary-green);
        color: white;
    }
    
    .btn-primary:hover {
        background: var(--dark-green);
        transform: translateY(-2px);
    }
    
    .btn-secondary {
        background: var(--light-gray);
        color: var(--dark-gray);
    }
    
    .btn-secondary:hover {
        background: #e0e0e0;
        transform: translateY(-2px);
    }
    
    /* ИНФО ПАНЕЛЬ */
    .info-panel {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: var(--white);
        padding: 15px 25px;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        border: 2px solid var(--light-green);
        z-index: 100;
        display: flex;
        align-items: center;
        gap: 15px;
        animation: slideIn 0.5s ease-out;
    }
    
    @keyframes slideIn {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    .online-count {
        font-weight: 600;
        color: var(--primary-green);
        font-size: 18px;
    }
    
    .notification {
        position: fixed;
        top: 20px;
        right: 20px;
        background: var(--white);
        padding: 15px 25px;
        border-radius: 15px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.15);
        border-left: 5px solid var(--primary-green);
        z-index: 100;
        animation: slideIn 0.5s ease-out;
        display: none;
    }
    
    /* УТИЛИТЫ */
    .hidden {
        display: none !important;
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* СКРОЛЛБАР */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--light-gray);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary-green);
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: var(--dark-green);
    }
    </style>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <div class="container">
        <!-- ЛЕВАЯ КОЛОНКА - КОНТАКТЫ -->
        <div class="sidebar-left">
            <div class="user-profile">
                <div class="user-avatar" id="userAvatar">?</div>
                <div class="user-info">
                    <div class="user-name" id="userName">Загрузка...</div>
                    <div class="user-id" id="userId" title="Нажмите для копирования">ID: ...</div>
                </div>
            </div>
            
            <div class="contacts-header">
                <h2><i class="fas fa-users"></i> Контакты</h2>
                <button class="add-contact-btn" id="addContactBtn">
                    <i class="fas fa-user-plus"></i>
                </button>
            </div>
            
            <div class="contacts-list" id="contactsList">
                <div class="empty-state">
                    <i class="fas fa-user-friends"></i>
                    <p>Нет контактов</p>
                    <p style="font-size: 14px; margin-top: 10px;">Добавьте контакты, чтобы начать общение</p>
                </div>
            </div>
        </div>
        
        <!-- ЦЕНТРАЛЬНАЯ КОЛОНКА - ЧАТ -->
        <div class="chat-container">
            <div class="chat-header">
                <div class="chat-info">
                    <h3 id="currentChatName">GrinMain</h3>
                    <div class="chat-status" id="currentChatStatus">
                        <span class="status-dot"></span>
                        <span>Выберите контакт для общения</span>
                    </div>
                </div>
                <div class="chat-actions">
                    <button class="action-btn call-btn" id="startCallFromChat" title="Позвонить">
                        <i class="fas fa-phone"></i>
                    </button>
                    <button class="action-btn message-btn" id="clearChat" title="Очистить чат">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            
            <div class="chat-messages" id="chatMessages">
                <div class="empty-state">
                    <i class="fas fa-comments"></i>
                    <p>Чат GrinMain</p>
                    <p style="font-size: 14px; margin-top: 10px;">Выберите контакт из списка слева</p>
                    <p style="font-size: 12px; margin-top: 20px; color: var(--primary-green);">
                        <i class="fas fa-shield-alt"></i> Ваши сообщения защищены шифрованием
                    </p>
                </div>
            </div>
            
            <div class="message-input-area hidden" id="messageInputArea">
                <input type="text" class="message-input" id="messageInput" 
                       placeholder="Введите сообщение..." autocomplete="off">
                <button class="send-btn" id="sendMessageBtn">
                    <i class="fas fa-paper-plane"></i>
                </button>
            </div>
        </div>
        
        <!-- ПРАВАЯ КОЛОНКА - ЗВОНКИ -->
        <div class="sidebar-right">
            <div class="call-header">
                <h2><i class="fas fa-phone-alt"></i> Звонки</h2>
                <p style="color: var(--gray); font-size: 14px;">Бесплатные голосовые звонки</p>
            </div>
            
            <div class="call-controls">
                <button class="call-btn-large call-start" id="startCallBtn">
                    <i class="fas fa-phone"></i>
                </button>
                <button class="call-btn-large call-end hidden" id="endCallBtn">
                    <i class="fas fa-phone-slash"></i>
                </button>
                
                <div class="call-status" id="callStatus">
                    Готов к звонкам
                </div>
                
                <audio id="remoteAudio" autoplay controls class="call-audio hidden"></audio>
                
                <div style="text-align: center; color: var(--gray); font-size: 14px; margin-top: 20px;">
                    <p><i class="fas fa-info-circle"></i> Для звонка выберите контакт</p>
                </div>
            </div>
        </div>
    </div>
    
    <!-- МОДАЛЬНОЕ ОКНО - НАСТРОЙКА ПРОФИЛЯ -->
    <div class="modal" id="profileModal">
        <div class="modal-content">
            <div class="modal-header">
                <h2><i class="fas fa-user-edit"></i> Ваш профиль</h2>
                <p>Настройте информацию о себе</p>
            </div>
            
            <div class="form-group">
                <label for="profileName"><i class="fas fa-user"></i> Имя пользователя</label>
                <input type="text" id="profileName" class="form-control" 
                       placeholder="Введите ваше имя" maxlength="20">
            </div>
            
            <div class="form-group">
                <label><i class="fas fa-id-card"></i> Ваш ID</label>
                <div style="background: var(--light-gray); padding: 12px; border-radius: 8px; font-family: monospace; font-size: 18px; text-align: center;"
                     id="profileUserId">
                    Загрузка...
                </div>
                <p style="font-size: 12px; color: var(--gray); margin-top: 5px;">
                    Этот ID уникален. Другие пользователи могут найти вас по нему.
                </p>
            </div>
            
            <div class="modal-buttons">
                <button class="btn btn-secondary" id="cancelProfileBtn">Отмена</button>
                <button class="btn btn-primary" id="saveProfileBtn">Сохранить</button>
            </div>
        </div>
    </div>
    
    <!-- МОДАЛЬНОЕ ОКНО - ДОБАВЛЕНИЕ КОНТАКТА -->
    <div class="modal" id="addContactModal">
        <div class="modal-content">
            <div class="modal-header">
                <h2><i class="fas fa-user-plus"></i> Добавить контакт</h2>
                <p>Введите ID пользователя для добавления</p>
            </div>
            
            <div class="form-group">
                <label for="contactIdInput"><i class="fas fa-hashtag"></i> ID пользователя</label>
                <input type="text" id="contactIdInput" class="form-control" 
                       placeholder="Введите 6-значный ID" pattern="[0-9]{6}" maxlength="6">
            </div>
            
            <div class="form-group">
                <label for="contactNameInput"><i class="fas fa-tag"></i> Имя контакта (опционально)</label>
                <input type="text" id="contactNameInput" class="form-control" 
                       placeholder="Введите имя для контакта" maxlength="20">
            </div>
            
            <div class="modal-buttons">
                <button class="btn btn-secondary" id="cancelAddContactBtn">Отмена</button>
                <button class="btn btn-primary" id="saveContactBtn">Добавить</button>
            </div>
        </div>
    </div>
    
    <!-- ИНФО ПАНЕЛЬ -->
    <div class="info-panel">
        <span><i class="fas fa-wifi"></i> Статус:</span>
        <span id="connectionStatus" style="color: var(--primary-green);">Подключение...</span>
        <span class="online-count" id="onlineCount">0 онлайн</span>
    </div>
    
    <!-- УВЕДОМЛЕНИЕ -->
    <div class="notification" id="notification">
        <i class="fas fa-bell"></i> <span id="notificationText"></span>
    </div>

    <script>
    // Глобальные переменные
    let ws = null;
    let myId = null;
    let myUsername = localStorage.getItem('grinmain_username') || '';
    let currentChatId = null;
    let peerConnection = null;
    let localStream = null;
    let contacts = JSON.parse(localStorage.getItem('grinmain_contacts') || '{}');
    let chatHistory = JSON.parse(localStorage.getItem('grinmain_chat_history') || '{}');
    let usersOnline = {};
    let typingTimeout = null;
    
    // DOM элементы
    const elements = {
        // Модальные окна
        profileModal: document.getElementById('profileModal'),
        addContactModal: document.getElementById('addContactModal'),
        
        // Профиль
        userAvatar: document.getElementById('userAvatar'),
        userName: document.getElementById('userName'),
        userId: document.getElementById('userId'),
        profileName: document.getElementById('profileName'),
        profileUserId: document.getElementById('profileUserId'),
        
        // Контакты
        contactsList: document.getElementById('contactsList'),
        addContactBtn: document.getElementById('addContactBtn'),
        contactIdInput: document.getElementById('contactIdInput'),
        contactNameInput: document.getElementById('contactNameInput'),
        
        // Чат
        currentChatName: document.getElementById('currentChatName'),
        currentChatStatus: document.getElementById('currentChatStatus'),
        chatMessages: document.getElementById('chatMessages'),
        messageInputArea: document.getElementById('messageInputArea'),
        messageInput: document.getElementById('messageInput'),
        sendMessageBtn: document.getElementById('sendMessageBtn'),
        startCallFromChat: document.getElementById('startCallFromChat'),
        
        // Звонки
        startCallBtn: document.getElementById('startCallBtn'),
        endCallBtn: document.getElementById('endCallBtn'),
        callStatus: document.getElementById('callStatus'),
        remoteAudio: document.getElementById('remoteAudio'),
        
        // Статус
        connectionStatus: document.getElementById('connectionStatus'),
        onlineCount: document.getElementById('onlineCount'),
        notification: document.getElementById('notification'),
        notificationText: document.getElementById('notificationText')
    };
    
    // Уведомления
    function showNotification(text, type = 'info') {
        elements.notificationText.textContent = text;
        elements.notification.style.borderLeftColor = 
            type === 'success' ? '#2ecc71' : 
            type === 'error' ? '#e74c3c' : '#3498db';
        elements.notification.style.display = 'block';
        
        setTimeout(() => {
            elements.notification.style.display = 'none';
        }, 3000);
    }
    
    // Инициализация
    async function init() {
        setupWebSocket();
        setupEventListeners();
        updateProfileDisplay();
        renderContacts();
        
        // Показать модальное окно профиля, если имя не задано
        if (!myUsername) {
            showProfileModal();
        }
        
        // Запрос уведомлений
        if (Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }
    
    // Настройка WebSocket
    function setupWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
        
        ws.onopen = () => {
            console.log('✅ Подключено к серверу GrinMain');
            elements.connectionStatus.textContent = 'Подключено';
            elements.connectionStatus.style.color = '#2ecc71';
            
            if (myUsername) {
                registerUser();
            }
        };
        
        ws.onmessage = async (event) => {
            try {
                const data = JSON.parse(event.data);
                
                switch (data.type) {
                    case 'your_id':
                        myId = data.data;
                        updateProfileDisplay();
                        break;
                        
                    case 'user_list':
                        usersOnline = data.users;
                        updateOnlineCount();
                        updateContactsStatus();
                        break;
                        
                    case 'message':
                        handleIncomingMessage(data);
                        break;
                        
                    case 'typing':
                        handleTypingIndicator(data);
                        break;
                        
                    case 'call_offer':
                        handleCallOffer(data);
                        break;
                        
                    case 'call_answer':
                        handleCallAnswer(data);
                        break;
                        
                    case 'ice_candidate':
                        handleIceCandidate(data);
                        break;
                        
                    case 'call_end':
                        handleCallEnd(data);
                        break;
                        
                    case 'user_online':
                        updateUserStatus(data.user_id, true);
                        break;
                        
                    case 'user_offline':
                        updateUserStatus(data.user_id, false);
                        break;
                }
            } catch (error) {
                console.error('Ошибка обработки сообщения:', error);
            }
        };
        
        ws.onerror = (error) => {
            console.error('WebSocket ошибка:', error);
            elements.connectionStatus.textContent = 'Ошибка подключения';
            elements.connectionStatus.style.color = '#e74c3c';
        };
        
        ws.onclose = () => {
            console.log('Соединение закрыто');
            elements.connectionStatus.textContent = 'Переподключение...';
            elements.connectionStatus.style.color = '#f39c12';
            setTimeout(setupWebSocket, 3000);
        };
    }
    
    // Регистрация пользователя
    function registerUser() {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({
                type: 'register',
                username: myUsername,
                user_id: myId
            }));
        }
    }
    
    // Обновление профиля
    function updateProfileDisplay() {
        const displayName = myUsername || `Гость_${myId ? myId.slice(-4) : '0000'}`;
        const firstLetter = displayName.charAt(0).toUpperCase();
        
        elements.userAvatar.textContent = firstLetter;
        elements.userName.textContent = displayName;
        
        if (myId) {
            elements.userId.textContent = `ID: ${myId}`;
            elements.profileUserId.textContent = myId;
        }
        
        // Сохраняем аватар в localStorage
        localStorage.setItem('grinmain_user_avatar', firstLetter);
    }
    
    // Отображение контактов
    function renderContacts() {
        const contactIds = Object.keys(contacts);
        
        if (contactIds.length === 0) {
            elements.contactsList.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-user-friends"></i>
                    <p>Нет контактов</p>
                    <p style="font-size: 14px; margin-top: 10px;">Добавьте контакты, чтобы начать общение</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        
        contactIds.forEach(contactId => {
            const contact = contacts[contactId];
            const isOnline = usersOnline[contactId]?.online || false;
            const lastMessage = chatHistory[contactId]?.messages?.[0];
            const lastMessageText = lastMessage ? 
                (lastMessage.sender === myId ? 'Вы: ' : '') + 
                lastMessage.text.substring(0, 25) + 
                (lastMessage.text.length > 25 ? '...' : '') : 'Нет сообщений';
            
            html += `
                <div class="contact-item ${currentChatId === contactId ? 'active' : ''}" 
                     data-id="${contactId}" onclick="selectContact('${contactId}')">
                    <div class="contact-avatar">${contact.name.charAt(0).toUpperCase()}</div>
                    <div class="contact-details">
                        <div class="contact-name">${contact.name}</div>
                        <div class="contact-status">
                            <span class="status-dot ${isOnline ? 'online' : ''}"></span>
                            <span>${isOnline ? 'в сети' : 'не в сети'}</span>
                            <span class="typing-indicator" id="typing-${contactId}" 
                                  style="display: none; margin-left: 10px;">печатает...</span>
                        </div>
                        <div style="font-size: 12px; color: #7f8c8d; margin-top: 3px;">${lastMessageText}</div>
                    </div>
                    <div class="contact-actions">
                        <button class="action-btn message-btn" onclick="selectContact('${contactId}', event)" 
                                title="Написать">
                            <i class="fas fa-comment"></i>
                        </button>
                        <button class="action-btn call-btn" onclick="startCallWithContact('${contactId}', event)" 
                                title="Позвонить">
                            <i class="fas fa-phone"></i>
                        </button>
                    </div>
                </div>
            `;
        });
        
        elements.contactsList.innerHTML = html;
    }
    
    // Добавление контакта
    function addContact(contactId, contactName = null) {
        if (contactId === myId) {
            showNotification('Нельзя добавить себя в контакты', 'error');
            return false;
        }
        
        if (contacts[contactId]) {
            showNotification('Контакт уже добавлен', 'error');
            return false;
        }
        
        const name = contactName || `Пользователь_${contactId.slice(-4)}`;
        contacts[contactId] = {
            id: contactId,
            name: name,
            added: Date.now()
        };
        
        localStorage.setItem('grinmain_contacts', JSON.stringify(contacts));
        renderContacts();
        showNotification(`Контакт "${name}" добавлен`, 'success');
        
        return true;
    }
    
    // Выбор контакта
    function selectContact(contactId, event = null) {
        if (event) event.stopPropagation();
        
        currentChatId = contactId;
        const contact = contacts[contactId];
        const isOnline = usersOnline[contactId]?.online || false;
        
        // Обновляем заголовок чата
        elements.currentChatName.textContent = contact.name;
        elements.currentChatStatus.innerHTML = `
            <span class="status-dot ${isOnline ? 'online' : ''}"></span>
            <span>${isOnline ? 'в сети' : 'не в сети'}</span>
            <span class="typing-indicator" id="current-typing" style="display: none; margin-left: 10px;">печатает...</span>
        `;
        
        // Показываем поле ввода сообщения
        elements.messageInputArea.classList.remove('hidden');
        elements.messageInput.focus();
        
        // Показываем кнопку звонка
        elements.startCallBtn.disabled = false;
        elements.startCallFromChat.disabled = false;
        
        // Рендерим историю сообщений
        renderChatMessages(contactId);
        
        // Обновляем выделение контакта
        document.querySelectorAll('.contact-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.id === contactId) {
                item.classList.add('active');
            }
        });
    }
    
    // Отправка сообщения
    function sendMessage() {
        const text = elements.messageInput.value.trim();
        if (!text || !currentChatId || !ws) return;
        
        const messageData = {
            type: 'message',
            target: currentChatId,
            text: text,
            timestamp: Date.now()
        };
        
        ws.send(JSON.stringify(messageData));
        
        // Сохраняем в историю
        if (!chatHistory[currentChatId]) {
            chatHistory[currentChatId] = { messages: [] };
        }
        
        chatHistory[currentChatId].messages.push({
            sender: myId,
            text: text,
            timestamp: messageData.timestamp
        });
        
        localStorage.setItem('grinmain_chat_history', JSON.stringify(chatHistory));
        
        // Очищаем поле ввода
        elements.messageInput.value = '';
        
        // Рендерим сообщение
        renderChatMessages(currentChatId);
        
        // Обновляем список контактов
        renderContacts();
    }
    
    // Рендер сообщений чата
    function renderChatMessages(contactId) {
        const messages = chatHistory[contactId]?.messages || [];
        
        if (messages.length === 0) {
            elements.chatMessages.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-comments"></i>
                    <p>Начните общение с ${contacts[contactId]?.name || 'пользователем'}</p>
                    <p style="font-size: 14px; margin-top: 10px;">Напишите первое сообщение</p>
                </div>
            `;
            return;
        }
        
        let html = '';
        
        messages.forEach(msg => {
            const isMine = msg.sender === myId;
            const time = new Date(msg.timestamp).toLocaleTimeString([], { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            const senderName = isMine ? myUsername : (contacts[contactId]?.name || 'Неизвестный');
            
            html += `
                <div class="message ${isMine ? 'outgoing' : 'incoming'}">
                    <div class="message-sender">${senderName}</div>
                    <div class="message-bubble">${msg.text}</div>
                    <div class="message-time">${time}</div>
                </div>
            `;
        });
        
        elements.chatMessages.innerHTML = html;
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    }
    
    // Обработка входящих сообщений
    function handleIncomingMessage(data) {
        const senderId = data.sender_id;
        
        // Если это новый контакт, добавляем его
        if (!contacts[senderId]) {
            const contactName = data.sender_name || `Пользователь_${senderId.slice(-4)}`;
            addContact(senderId, contactName);
        }
        
        // Сохраняем сообщение
        if (!chatHistory[senderId]) {
            chatHistory[senderId] = { messages: [] };
        }
        
        chatHistory[senderId].messages.push({
            sender: senderId,
            text: data.text,
            timestamp: data.timestamp
        });
        
        localStorage.setItem('grinmain_chat_history', JSON.stringify(chatHistory));
        
        // Если открыт чат с отправителем - обновляем
        if (currentChatId === senderId) {
            renderChatMessages(senderId);
        }
        
        // Обновляем список контактов
        renderContacts();
        
        // Уведомление
        if (currentChatId !== senderId && Notification.permission === 'granted') {
            new Notification(`GrinMain: новое сообщение`, {
                body: `${contacts[senderId]?.name || 'Неизвестный'}: ${data.text}`,
                icon: 'https://cdn-icons-png.flaticon.com/512/733/733585.png'
            });
        }
    }
    
    // Звонки
    function startCallWithContact(contactId, event = null) {
        if (event) event.stopPropagation();
        
        if (!currentChatId || currentChatId !== contactId) {
            selectContact(contactId);
        }
        startCall();
    }
    
    async function startCall() {
        if (!currentChatId) {
            showNotification('Выберите контакт для звонка', 'error');
            return;
        }
        
        try {
            elements.callStatus.textContent = 'Подготовка микрофона...';
            elements.callStatus.classList.add('ringing');
            
            localStream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            });
            
            createPeerConnection();
            
            const offer = await peerConnection.createOffer({
                offerToReceiveAudio: true
            });
            
            await peerConnection.setLocalDescription(offer);
            
            ws.send(JSON.stringify({
                type: 'call_offer',
                target: currentChatId,
                offer: offer
            }));
            
            elements.callStatus.textContent = `Звонок ${contacts[currentChatId]?.name}...`;
            elements.startCallBtn.classList.add('hidden');
            elements.endCallBtn.classList.remove('hidden');
            elements.startCallFromChat.disabled = true;
            
        } catch (error) {
            console.error('Ошибка звонка:', error);
            elements.callStatus.textContent = 'Ошибка: ' + error.message;
            elements.callStatus.classList.remove('ringing');
        }
    }
    
    function createPeerConnection() {
        peerConnection = new RTCPeerConnection({
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' }
            ]
        });
        
        peerConnection.onicecandidate = (event) => {
            if (event.candidate && currentChatId) {
                ws.send(JSON.stringify({
                    type: 'ice_candidate',
                    target: currentChatId,
                    candidate: event.candidate
                }));
            }
        };
        
        peerConnection.ontrack = (event) => {
            elements.remoteAudio.srcObject = event.streams[0];
            elements.remoteAudio.classList.remove('hidden');
            elements.callStatus.textContent = '✅ Разговор начался';
            elements.callStatus.classList.remove('ringing');
        };
        
        if (localStream) {
            localStream.getTracks().forEach(track => {
                peerConnection.addTrack(track, localStream);
            });
        }
    }
    
    async function handleCallOffer(data) {
        if (!confirm(`Входящий звонок от ${data.sender_name || 'пользователя'}. Принять?`)) {
            ws.send(JSON.stringify({
                type: 'call_end',
                target: data.sender_id
            }));
            return;
        }
        
        // Добавляем контакт, если его нет
        if (!contacts[data.sender_id]) {
            addContact(data.sender_id, data.sender_name);
        }
        
        selectContact(data.sender_id);
        
        try {
            localStream = await navigator.mediaDevices.getUserMedia({ 
                audio: true
            });
            
            if (!peerConnection) createPeerConnection();
            
            await peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer));
            const answer = await peerConnection.createAnswer();
            await peerConnection.setLocalDescription(answer);
            
            ws.send(JSON.stringify({
                type: 'call_answer',
                target: data.sender_id,
                answer: answer
            }));
            
            elements.callStatus.textContent = 'В разговоре...';
            elements.startCallBtn.classList.add('hidden');
            elements.endCallBtn.classList.remove('hidden');
            elements.startCallFromChat.disabled = true;
            
        } catch (error) {
            console.error('Ошибка принятия звонка:', error);
            endCall();
        }
    }
    
    async function handleCallAnswer(data) {
        if (peerConnection) {
            await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));
        }
    }
    
    async function handleIceCandidate(data) {
        if (peerConnection) {
            try {
                await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
            } catch (error) {
                console.error('Ошибка добавления ICE кандидата:', error);
            }
        }
    }
    
    function handleCallEnd(data) {
        endCall();
        if (data.sender_id) {
            showNotification(`Звонок с ${contacts[data.sender_id]?.name || 'пользователем'} завершен`, 'info');
        }
    }
    
    function endCall() {
        if (peerConnection) {
            peerConnection.close();
            peerConnection = null;
        }
        
        if (localStream) {
            localStream.getTracks().forEach(track => track.stop());
            localStream = null;
        }
        
        elements.remoteAudio.srcObject = null;
        elements.remoteAudio.classList.add('hidden');
        elements.startCallBtn.classList.remove('hidden');
        elements.endCallBtn.classList.add('hidden');
        elements.callStatus.textContent = 'Готов к звонкам';
        elements.callStatus.classList.remove('ringing');
        elements.startCallFromChat.disabled = false;
        
        if (currentChatId) {
            ws.send(JSON.stringify({
                type: 'call_end',
                target: currentChatId
            }));
        }
    }
    
    // Индикатор набора текста
    function handleTypingIndicator(data) {
        const typingElement = document.getElementById(`typing-${data.sender_id}`);
        if (typingElement) {
            typingElement.style.display = data.typing ? 'inline' : 'none';
        }
        
        if (currentChatId === data.sender_id) {
            const currentTyping = document.getElementById('current-typing');
            if (currentTyping) {
                currentTyping.style.display = data.typing ? 'inline' : 'none';
            }
        }
    }
    
    function sendTypingIndicator(typing) {
        if (currentChatId && ws) {
            ws.send(JSON.stringify({
                type: 'typing',
                target: currentChatId,
                typing: typing
            }));
        }
    }
    
    // Обновление статуса пользователей
    function updateUserStatus(userId, online) {
        if (usersOnline[userId]) {
            usersOnline[userId].online = online;
        }
        
        updateContactsStatus();
        updateOnlineCount();
        
        if (currentChatId === userId) {
            const statusDot = document.querySelector('#currentChatStatus .status-dot');
            const statusText = document.querySelector('#currentChatStatus span:nth-child(2)');
            
            if (statusDot && statusText) {
                statusDot.classList.toggle('online', online);
                statusText.textContent = online ? 'в сети' : 'не в сети';
            }
        }
    }
    
    function updateContactsStatus() {
        Object.keys(contacts).forEach(contactId => {
            const contactItem = document.querySelector(`.contact-item[data-id="${contactId}"]`);
            if (contactItem) {
                const statusDot = contactItem.querySelector('.status-dot');
                const statusText = contactItem.querySelector('.contact-status span:nth-child(2)');
                
                if (statusDot && statusText) {
                    const isOnline = usersOnline[contactId]?.online || false;
                    statusDot.classList.toggle('online', isOnline);
                    statusText.textContent = isOnline ? 'в сети' : 'не в сети';
                }
            }
        });
    }
    
    function updateOnlineCount() {
        const onlineUsers = Object.values(usersOnline).filter(user => user.online).length;
        elements.onlineCount.textContent = `${onlineUsers} онлайн`;
    }
    
    // Модальные окна
    function showProfileModal() {
        elements.profileName.value = myUsername || '';
        if (myId) {
            elements.profileUserId.textContent = myId;
        }
        elements.profileModal.style.display = 'flex';
    }
    
    function hideProfileModal() {
        elements.profileModal.style.display = 'none';
    }
    
    function showAddContactModal() {
        elements.contactIdInput.value = '';
        elements.contactNameInput.value = '';
        elements.addContactModal.style.display = 'flex';
        elements.contactIdInput.focus();
    }
    
    function hideAddContactModal() {
        elements.addContactModal.style.display = 'none';
    }
    
    // Настройка обработчиков событий
    function setupEventListeners() {
        // Профиль
        elements.userId.addEventListener('click', () => {
            navigator.clipboard.writeText(myId).then(() => {
                showNotification('ID скопирован в буфер обмена', 'success');
            });
        });
        
        document.getElementById('saveProfileBtn').addEventListener('click', () => {
            const newUsername = elements.profileName.value.trim();
            if (newUsername.length >= 2 && newUsername.length <= 20) {
                myUsername = newUsername;
                localStorage.setItem('grinmain_username', myUsername);
                updateProfileDisplay();
                registerUser();
                hideProfileModal();
                showNotification('Профиль обновлен', 'success');
            } else {
                showNotification('Имя должно быть от 2 до 20 символов', 'error');
            }
        });
        
        document.getElementById('cancelProfileBtn').addEventListener('click', hideProfileModal);
        
        // Добавление контактов
        elements.addContactBtn.addEventListener('click', showAddContactModal);
        
        document.getElementById('saveContactBtn').addEventListener('click', () => {
            const contactId = elements.contactIdInput.value.trim();
            const contactName = elements.contactNameInput.value.trim();
            
            if (!/^\d{6}$/.test(contactId)) {
                showNotification('Введите 6-значный ID пользователя', 'error');
                return;
            }
            
            if (addContact(contactId, contactName || null)) {
                hideAddContactModal();
            }
        });
        
        document.getElementById('cancelAddContactBtn').addEventListener('click', hideAddContactModal);
        
        // Чат
        elements.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        elements.messageInput.addEventListener('input', () => {
            clearTimeout(typingTimeout);
            sendTypingIndicator(true);
            
            typingTimeout = setTimeout(() => {
                sendTypingIndicator(false);
            }, 1000);
        });
        
        elements.sendMessageBtn.addEventListener('click', sendMessage);
        
        // Звонки
        elements.startCallBtn.addEventListener('click', startCall);
        elements.endCallBtn.addEventListener('click', endCall);
        elements.startCallFromChat.addEventListener('click', startCall);
        
        // Закрытие модальных окон по клику вне их
        window.addEventListener('click', (event) => {
            if (event.target === elements.profileModal) {
                hideProfileModal();
            }
            if (event.target === elements.addContactModal) {
                hideAddContactModal();
            }
        });
    }
    
    // Глобальные функции
    window.selectContact = selectContact;
    window.startCallWithContact = startCallWithContact;
    window.startCall = startCall;
    window.endCall = endCall;
    
    // Запуск приложения
    document.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>"""

# ========== CloudPub функция ==========
async def publish_with_cloudpub(local_port=8080):
    """Публикует локальный сервер через CloudPub"""
    global cloudpub_info
    
    try:
        print("\n" + "="*50)
        print("🌐 ПОДКЛЮЧЕНИЕ К CLOUDPUB")
        print("="*50)
        
        conn = Connection(email=CLOUDPUB_EMAIL, password=CLOUDPUB_PASSWORD)
        
        print(f"📡 Публикую localhost:{local_port}...")
        endpoint = conn.publish(
            Protocol.HTTP,
            f"localhost:{local_port}",
            name="GrinMain Chat",
            auth=Auth.NONE
        )
        
        public_url = endpoint.url
        print(f"✅ СЕРВИС ОПУБЛИКОВАН!")
        print(f"🔗 Публичный URL: {public_url}")
        print("="*50)
        print("📱 Отправьте эту ссылку друзьям для подключения")
        print("="*50)
        
        # Обновляем HTML с публичным URL
        global HTML_PAGE
        html_with_url = HTML_PAGE.replace(
            '<!-- ИНФО ПАНЕЛЬ -->',
            f'<!-- ИНФО ПАНЕЛЬ -->\n<div style="position: fixed; top: 20px; left: 20px; background: #2ecc71; color: white; padding: 10px 20px; border-radius: 10px; z-index: 100; font-size: 14px; box-shadow: 0 5px 15px rgba(46, 204, 113, 0.3);">\n    <i class="fas fa-link"></i> Ссылка для друзей:\n    <div style="font-family: monospace; font-size: 12px; margin-top: 5px; background: rgba(255,255,255,0.2); padding: 5px 10px; border-radius: 5px;">\n        {public_url}\n    </div>\n</div>'
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

# ========== WebSocket обработчик ==========
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    # Генерируем уникальный 6-значный ID
    user_id = str(random.randint(100000, 999999))
    
    # Добавляем пользователя
    users[user_id] = {
        'ws': ws,
        'username': 'Гость',
        'online': True,
        'last_seen': time.time(),
        'user_id': user_id
    }
    
    connected_clients[user_id] = ws
    
    print(f"👤 {user_id} подключился")
    
    try:
        # Отправляем ID пользователю
        await ws.send_json({'type': 'your_id', 'data': user_id})
        
        # Отправляем список пользователей всем
        await broadcast_user_list()
        
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    
                    # Обновляем время последней активности
                    users[user_id]['last_seen'] = time.time()
                    
                    # Обрабатываем разные типы сообщений
                    if data['type'] == 'register':
                        # Регистрация имени пользователя
                        users[user_id]['username'] = data['username']
                        await broadcast_user_list()
                        await broadcast_user_status(user_id, 'online')
                        
                    elif data['type'] == 'message':
                        # Текстовое сообщение
                        target_id = data.get('target')
                        if target_id in users:
                            # Сохраняем сообщение
                            messages.append({
                                'from': user_id,
                                'from_name': users[user_id]['username'],
                                'to': target_id,
                                'text': data['text'],
                                'timestamp': data.get('timestamp', time.time())
                            })
                            # Пересылаем получателю
                            await users[target_id]['ws'].send_json({
                                'type': 'message',
                                'sender_id': user_id,
                                'sender_name': users[user_id]['username'],
                                'text': data['text'],
                                'timestamp': data.get('timestamp', time.time())
                            })
                            
                    elif data['type'] == 'typing':
                        # Индикатор набора текста
                        target_id = data.get('target')
                        if target_id in users:
                            await users[target_id]['ws'].send_json({
                                'type': 'typing',
                                'sender_id': user_id,
                                'typing': data.get('typing', False)
                            })
                            
                    elif data['type'] in ['call_offer', 'call_answer', 'ice_candidate', 'call_end']:
                        # Сигнализация WebRTC
                        target_id = data.get('target')
                        if target_id in users:
                            # Добавляем имя отправителя для call_offer
                            if data['type'] == 'call_offer':
                                data['sender_name'] = users[user_id]['username']
                            await users[target_id]['ws'].send_json(data)
                            
                except json.JSONDecodeError:
                    print(f"❌ Ошибка JSON от {user_id}")
                except KeyError as e:
                    print(f"❌ Ошибка ключа от {user_id}: {e}")
                    
    except Exception as e:
        print(f"❌ Ошибка у {user_id}: {e}")
        
    finally:
        # Удаляем пользователя при отключении
        if user_id in users:
            users[user_id]['online'] = False
            await broadcast_user_status(user_id, 'offline')
            await broadcast_user_list()
            print(f"👋 {user_id} отключился")
        
        if user_id in connected_clients:
            del connected_clients[user_id]

    return ws

async def broadcast_user_list():
    """Рассылает актуальный список пользователей всем"""
    user_list = {
        uid: {
            'username': users[uid]['username'],
            'online': users[uid]['online'],
            'last_seen': users[uid]['last_seen'],
            'user_id': users[uid]['user_id']
        }
        for uid in users
    }
    
    for uid, user_data in users.items():
        if user_data['ws'] and not user_data['ws'].closed:
            try:
                await user_data['ws'].send_json({
                    'type': 'user_list',
                    'users': user_list
                })
            except:
                pass

async def broadcast_user_status(user_id, status):
    """Рассылает статус пользователя всем"""
    for uid, user_data in users.items():
        if user_data['ws'] and not user_data['ws'].closed and uid != user_id:
            try:
                await user_data['ws'].send_json({
                    'type': 'user_online' if status == 'online' else 'user_offline',
                    'user_id': user_id,
                    'username': users[user_id]['username']
                })
            except:
                pass

# ========== HTTP обработчики ==========
async def http_handler(request):
    return web.Response(text=HTML_PAGE, content_type='text/html')

# ========== Основной сервер ==========
async def cleanup_users():
    """Очистка неактивных пользователей"""
    while True:
        await asyncio.sleep(60)
        current_time = time.time()
        to_remove = []
        
        for user_id, user_data in users.items():
            if current_time - user_data['last_seen'] > 300:  # 5 минут
                to_remove.append(user_id)
        
        for user_id in to_remove:
            if user_id in users and users[user_id]['ws']:
                try:
                    await users[user_id]['ws'].close()
                except:
                    pass
            if user_id in users:
                del users[user_id]
            if user_id in connected_clients:
                del connected_clients[user_id]
        
        if to_remove:
            await broadcast_user_list()
            print(f"🧹 Удалено {len(to_remove)} неактивных пользователей")

async def main():
    print("\n" + "="*60)
    print("🚀 GRINMAIN - БЕСПЛАТНЫЕ ЗВОНКИ И ЧАТ")
    print("="*60)
    print("🟢 Тема: Бело-зеленая")
    print("📞 Функции: Голосовые звонки, Текстовый чат, Контакты")
    print("🌐 Публикация через CloudPub")
    print("="*60)
    
    app = web.Application()
    app.router.add_get('/', http_handler)
    app.router.add_get('/ws', websocket_handler)
    
    # CORS middleware
    async def cors_middleware(app, handler):
        async def middleware_handler(request):
            response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response
        return middleware_handler
    
    app.middlewares.append(cors_middleware)
    
    # Запускаем сервер
    runner = web.AppRunner(app)
    await runner.setup()
    
    LOCAL_PORT = 8080
    site = web.TCPSite(runner, '0.0.0.0', LOCAL_PORT)
    await site.start()
    
    print(f"✅ ЛОКАЛЬНЫЙ СЕРВЕР ЗАПУЩЕН!")
    print(f"🌐 Локальный URL: http://localhost:{LOCAL_PORT}")
    print("="*60)
    
    # Запускаем очистку неактивных пользователей
    asyncio.create_task(cleanup_users())
    
    # Публикуем через CloudPub
    if CLOUDPUB_AVAILABLE:
        await publish_with_cloudpub(LOCAL_PORT)
    else:
        print("⚠️  CloudPub не установлен. Установите: pip install cloudpub-python-sdk")
        print("   Чат будет работать только в локальной сети")
        print("="*60)
        print("📱 Для доступа с телефона в той же Wi-Fi:")
        print("   http://ваш-IP-адрес:8080")
        print("="*60)
    
    try:
        await asyncio.Future()  # Бесконечное ожидание
    except KeyboardInterrupt:
        print("\n🛑 Останавливаю сервер...")
        
        # Отменяем публикацию CloudPub
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
        print("\n👋 GrinMain остановлен")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        print("\n🔧 Решение проблем:")
        print("1. Установите зависимости: pip install aiohttp cloudpub-python-sdk")
        print("2. Проверьте интернет-соединение")
        print("3. Проверьте учетные данные CloudPub")
        