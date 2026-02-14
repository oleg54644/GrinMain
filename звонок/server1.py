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
CLOUDPUB_PASSWORD = "5464475337745l"  # ⚠️ В реальном приложении храните в переменных окружения!

# ========== HTML страница ==========
HTML_PAGE = """<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><title>📞 Голосовой чат</title>
<style>body{font-family:Arial;padding:20px;max-width:500px;margin:auto}
#status{padding:10px;background:#e0e0e0;border-radius:5px;margin:10px 0}
button{padding:10px 15px;margin:5px;border:none;border-radius:5px;cursor:pointer}
#callBtn{background:#4CAF50;color:white}#endBtn{background:#f44336;color:white}
.url-box{background:#fff3cd;padding:10px;border-radius:5px;margin:10px 0;word-break:break-all}</style>
</head>
<body>
<h1>📞 Голосовой чат</h1>
<div id="status"><strong>Ваш ID:</strong> <span id="myId">загрузка...</span></div>
<div id="cloudpubUrl" style="display:none;"><strong>🌐 Публичный URL:</strong>
<div class="url-box" id="publicUrl"></div><small>Отправьте эту ссылку другу</small></div>
<div><input type="text" id="targetId" placeholder="ID друга"><br>
<button id="callBtn">Позвонить</button><button id="endBtn" disabled>Завершить</button></div>
<div id="callStatus">Статус: Ожидание...</div><audio id="remoteAudio" autoplay></audio>

<script>
let ws, myId, targetId, peerConnection, localStream;
function connectWebSocket() {
    ws = new WebSocket((window.location.protocol === 'https:' ? 'wss:' : 'ws:') + '//' + window.location.host + '/ws');
    ws.onopen = () => console.log('✅ Подключен');
    ws.onmessage = async (e) => {
        try{const d=JSON.parse(e.data);
            if(d.type==='your_id'){myId=d.data;document.getElementById('myId').textContent=myId;updateStatus('Готов! ID: '+myId);}
            else if(d.type==='offer')await handleOffer(d);
            else if(d.type==='answer')await handleAnswer(d);
            else if(d.type==='ice_candidate')await handleIceCandidate(d);
        }catch(e){console.error(e);}
    };
    ws.onerror = () => updateStatus('Ошибка соединения');
}
async function startCall(){
    targetId=document.getElementById('targetId').value.trim();
    if(!targetId)return alert('Введите ID друга!');
    updateStatus('Запрашиваю микрофон...');
    try{
        localStream=await navigator.mediaDevices.getUserMedia({audio:true,video:false});
        createPeerConnection();
        const offer=await peerConnection.createOffer();
        await peerConnection.setLocalDescription(offer);
        ws.send(JSON.stringify({type:'offer',target:targetId,offer:offer}));
        updateStatus('Звоню '+targetId+'...');
        document.getElementById('callBtn').disabled=true;
        document.getElementById('endBtn').disabled=false;
    }catch(err){alert('Ошибка: '+err.message);}
}
function createPeerConnection(){
    peerConnection=new RTCPeerConnection({iceServers:[{urls:'stun:stun.l.google.com:19302'}]});
    peerConnection.onicecandidate=(e)=>{if(e.candidate&&targetId)ws.send(JSON.stringify({type:'ice_candidate',target:targetId,candidate:e.candidate}));};
    peerConnection.ontrack=(e)=>{const a=document.getElementById('remoteAudio');if(!a.srcObject){a.srcObject=e.streams[0];updateStatus('✅ Разговор начался!');}};
    if(localStream)localStream.getTracks().forEach(t=>peerConnection.addTrack(t,localStream));
}
async function handleOffer(data){
    updateStatus('Входящий звонок...');
    if(!localStream)try{localStream=await navigator.mediaDevices.getUserMedia({audio:true,video:false});}catch{return alert('Нет микрофона');}
    targetId=data.sender_id;
    if(!peerConnection)createPeerConnection();
    await peerConnection.setRemoteDescription(new RTCSessionDescription(data.offer));
    const answer=await peerConnection.createAnswer();
    await peerConnection.setLocalDescription(answer);
    ws.send(JSON.stringify({type:'answer',target:targetId,answer:answer}));
    document.getElementById('callBtn').disabled=true;
    document.getElementById('endBtn').disabled=false;
}
async function handleAnswer(data){if(peerConnection)await peerConnection.setRemoteDescription(new RTCSessionDescription(data.answer));}
async function handleIceCandidate(data){if(peerConnection)await peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));}
function endCall(){
    if(peerConnection)peerConnection.close();
    if(localStream)localStream.getTracks().forEach(t=>t.stop());
    document.getElementById('remoteAudio').srcObject=null;
    document.getElementById('callBtn').disabled=false;
    document.getElementById('endBtn').disabled=true;
    updateStatus('Звонок завершен');
}
function updateStatus(msg){document.getElementById('callStatus').textContent='Статус: '+msg;}
window.onload=()=>{connectWebSocket();document.getElementById('callBtn').onclick=startCall;document.getElementById('endBtn').onclick=endCall;};
</script></body></html>"""

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
        await ws.send_json({"type": "your_id", "data": client_id})
        
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                data = json.loads(msg.data)
                data["sender_id"] = client_id
                target_id = data.get("target")
                
                if target_id in connected_clients:
                    await connected_clients[target_id].send_json(data)
                    # print(f"  {client_id} -> {target_id}: {data['type'][:20]}")
                    
    except Exception as e:
        print(f"❌ Ошибка у {client_id}: {e}")
    finally:
        if client_id in connected_clients:
            del connected_clients[client_id]
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
        print("Попробуйте:")
        print("1. Установить зависимости: pip install aiohttp cloudpub-python-sdk")
        print("2. Проверить интернет-соединение")
        print("3. Проверить учетные данные CloudPub")
        