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

# ========== HTML страница с кнопками принятия звонка ==========
HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>📞 Голосовой чат</title>
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
    </style>
</head>
<body>
    <h1>📞 Голосовой чат</h1>
    
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
    <audio id="remoteAudio" autoplay></audio>

    <script>
        let ws, myId, targetId, callerId, peerConnection, localStream;
        let isInitiator = false;
        let pendingOffer = null;
        
        function connectWebSocket() {
            ws = new WebSocket((window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/ws');
            
            ws.onopen = () => {
                console.log('✅ WebSocket подключен');
                updateStatus('Подключено к серверу', 'online');
            };
            
            ws.onmessage = async (e) => {
                try {
                    const data = JSON.parse(e.data);
                    console.log('Получено сообщение:', data.type);
                    
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
                    console.error('Ошибка обработки сообщения:', err);
                }
            };
            
            ws.onclose = () => {
                updateStatus('Соединение потеряно', 'offline');
                setTimeout(connectWebSocket, 3000);
            };
            
            ws.onerror = () => {
                updateStatus('Ошибка соединения', 'offline');
            };
        }
        
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
                // Запрашиваем доступ к микрофону
                localStream = await navigator.mediaDevices.getUserMedia({
                    audio: {
                        echoCancellation: true,
                        noiseSuppression: true,
                        autoGainControl: true
                    },
                    video: false
                });
                
                isInitiator = true;
                createPeerConnection();
                
                // Создаем предложение для звонка
                const offer = await peerConnection.createOffer({
                    offerToReceiveAudio: true,
                    offerToReceiveVideo: false
                });
                
                await peerConnection.setLocalDescription(offer);
                
                // Отправляем предложение целевому пользователю
                ws.send(JSON.stringify({
                    type: 'offer',
                    target: targetId,
                    offer: offer
                }));
                
                updateStatus(`Звоню ${targetId}...`, 'calling');
                
                // Обновляем UI
                document.getElementById('callBtn').disabled = true;
                document.getElementById('endBtn').disabled = false;
                document.getElementById('targetId').disabled = true;
                
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
            
            // Обработка ICE кандидатов
            peerConnection.onicecandidate = (event) => {
                if (event.candidate && targetId) {
                    ws.send(JSON.stringify({
                        type: 'ice_candidate',
                        target: targetId,
                        candidate: event.candidate
                    }));
                }
            };
            
            // Получение удаленного потока
            peerConnection.ontrack = (event) => {
                const audioElement = document.getElementById('remoteAudio');
                if (!audioElement.srcObject) {
                    audioElement.srcObject = event.streams[0];
                    updateStatus('✅ Разговор начался! Говорите...', 'online');
                }
            };
            
            // Изменение состояния соединения
            peerConnection.onconnectionstatechange = () => {
                console.log('Состояние соединения:', peerConnection.connectionState);
                if (peerConnection.connectionState === 'disconnected' ||
                    peerConnection.connectionState === 'failed' ||
                    peerConnection.connectionState === 'closed') {
                    // resetCallState();
                }
            };
            
            // Добавляем локальный поток, если он есть
            if (localStream) {
                localStream.getTracks().forEach(track => {
                    peerConnection.addTrack(track, localStream);
                });
            }
        }
        
        function handleIncomingCall(data) {
            // Показываем окно входящего звонка
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
                // Скрываем окно входящего звонка
                document.getElementById('incomingCall').style.display = 'none';
                
                // Запрашиваем доступ к микрофону
                if (!localStream) {
                    localStream = await navigator.mediaDevices.getUserMedia({
                        audio: {
                            echoCancellation: true,
                            noiseSuppression: true,
                            autoGainControl: true
                        },
                        video: false
                    });
                }
                
                targetId = callerId;
                isInitiator = false;
                createPeerConnection();
                
                // Устанавливаем удаленное описание (предложение звонящего)
                await peerConnection.setRemoteDescription(new RTCSessionDescription(pendingOffer));
                
                // Создаем ответ
                const answer = await peerConnection.createAnswer();
                await peerConnection.setLocalDescription(answer);
                
                // Отправляем ответ
                ws.send(JSON.stringify({
                    type: 'answer',
                    target: targetId,
                    answer: answer
                }));
                
                // Обновляем UI
                document.getElementById('callBtn').disabled = true;
                document.getElementById('endBtn').disabled = false;
                document.getElementById('targetId').disabled = true;
                
                updateStatus('✅ Звонок принят! Говорите...', 'online');
                
            } catch(err) {
                console.error('Ошибка при принятии звонка:', err);
                alert(`Ошибка: ${err.message}`);
                resetCallState();
            }
        }
        
        function rejectCall() {
            // Отправляем сообщение об отклонении
            if (callerId) {
                ws.send(JSON.stringify({
                    type: 'call_rejected',
                    target: callerId,
                    reason: 'Звонок отклонен'
                }));
            }
            
            // Скрываем окно входящего звонка
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
        
        function endCall() {
            // Отправляем сообщение о завершении звонка
            if (targetId && ws.readyState === WebSocket.OPEN) {
                if (isInitiator) {
                    ws.send(JSON.stringify({
                        type: 'call_canceled',
                        target: targetId
                    }));
                }
            }
            
            // Закрываем PeerConnection
            if (peerConnection) {
                peerConnection.close();
                peerConnection = null;
            }
            
            // Останавливаем локальные треки
            if (localStream) {
                localStream.getTracks().forEach(track => track.stop());
                localStream = null;
            }
            
            // Сбрасываем аудио элемент
            document.getElementById('remoteAudio').srcObject = null;
            
            // Сбрасываем состояние
            resetCallState();
            
            updateStatus('Звонок завершен', 'online');
        }
        
        function resetCallState() {
            // Включаем кнопки
            document.getElementById('callBtn').disabled = false;
            document.getElementById('endBtn').disabled = true;
            document.getElementById('targetId').disabled = false;
            
            // Скрываем окно входящего звонка
            document.getElementById('incomingCall').style.display = 'none';
            
            // Сбрасываем переменные
            targetId = null;
            callerId = null;
            pendingOffer = null;
            isInitiator = false;
        }
        
        function updateStatus(message, statusClass = '') {
            const statusElement = document.getElementById('callStatus');
            const indicator = document.getElementById('statusIndicator');
            
            statusElement.textContent = `Статус: ${message}`;
            
            // Обновляем индикатор статуса
            indicator.className = 'status-indicator';
            if (statusClass) {
                indicator.classList.add(statusClass);
            }
            
            console.log(`Статус: ${message}`);
        }
        
        // Инициализация при загрузке страницы
        window.onload = () => {
            connectWebSocket();
            
            // Назначаем обработчики событий
            document.getElementById('callBtn').onclick = startCall;
            document.getElementById('endBtn').onclick = endCall;
            document.getElementById('acceptBtn').onclick = acceptCall;
            document.getElementById('rejectBtn').onclick = rejectCall;
            
            // Обработка нажатия Enter в поле ввода ID
            document.getElementById('targetId').addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    startCall();
                }
            });
            
            // Предупреждение при закрытии страницы во время звонка
            window.addEventListener('beforeunload', (e) => {
                if (peerConnection && peerConnection.connectionState === 'connected') {
                    e.preventDefault();
                    e.returnValue = 'У вас активный звонок. Вы уверены, что хотите закрыть страницу?';
                    return e.returnValue;
                }
            });
        };
    </script>
</body>
</html>"""

# ========== CloudPub функция ==========
async def publish_with_cloudpub(local_port=8080):
    """Публикует локальный сервер через CloudPub"""
    global cloudpub_info
    
    try:
        print("\n🔗 Подключаюсь к CloudPub...")
        print(f"📧 Email: {CLOUDPUB_EMAIL}")
        print("🔑 Пароль: ************")  # Скрываем пароль в выводе
        
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

# ========== Основной сервер ==========
connected_clients = {}
pending_calls = {}  # Для отслеживания ожидающих звонков

async def http_handler(request):
    """Отдаем HTML страницу"""
    return web.Response(text=HTML_PAGE, content_type='text/html')

async def websocket_handler(request):
    """Обрабатываем WebSocket соединения"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    client_id = f"user_{len(connected_clients) + 1}"
    connected_clients[client_id] = ws
    
    print(f"👤 {client_id} подключился")
    
    try:
        # Отправляем клиенту его ID
        await ws.send_json({"type": "your_id", "data": client_id})
        
        # Обрабатываем сообщения от клиента
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    data["sender_id"] = client_id
                    target_id = data.get("target")
                    
                    if target_id in connected_clients:
                        await connected_clients[target_id].send_json(data)
                        
                        # Логируем тип сообщения
                        msg_type = data.get('type', 'unknown')
                        if msg_type in ['offer', 'answer', 'ice_candidate']:
                            print(f"  📨 {client_id} -> {target_id}: {msg_type}")
                        elif msg_type in ['call_rejected', 'call_canceled']:
                            print(f"  ❌ {client_id} -> {target_id}: {msg_type}")
                            
                    else:
                        # Если целевой пользователь не найден
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
        # Удаляем клиента при отключении
        if client_id in connected_clients:
            del connected_clients[client_id]
            
        # Отменяем все ожидающие звонки от этого пользователя
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
    """Запускаем сервер"""
    print("=" * 60)
    print("🎧 ГОЛОСОВОЙ ЧАТ С CLOUDPUB")
    print("=" * 60)
    
    app = web.Application()
    app.router.add_get('/', http_handler)
    app.router.add_get('/ws', websocket_handler)
    
    # Настраиваем CORS для всех запросов
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
    print("=" * 60)
    
    # Публикуем через CloudPub
    if CLOUDPUB_AVAILABLE:
        await publish_with_cloudpub(LOCAL_PORT)
    else:
        print("⚠️  CloudPub не установлен. Установите: pip install cloudpub-python-sdk")
        print("   Звонок будет работать только в локальной сети")
        print("=" * 60)
        print("📱 Для телефона в той же Wi-Fi:")
        print("   http://ваш-IP-адрес:8080")
        print("=" * 60)
    
    # Ждем вечно
    try:
        await asyncio.Future()
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
        print("\n👋 Сервер остановлен")
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        print("\nПопробуйте:")
        print("1. Установить зависимости: pip install aiohttp cloudpub-python-sdk")
        print("2. Проверить интернет-соединение")
        print("3. Проверить учетные данные CloudPub")
        print("4. Проверить, что порт 8080 свободен")
        