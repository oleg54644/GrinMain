import os
import sys
import time
import threading
import subprocess
from collections import deque
from urllib.parse import urlparse, unquote
import shutil

from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify, abort
from werkzeug.utils import secure_filename
import requests

app = Flask(__name__)
app.secret_key = 'super-secret-key-change-in-production'
app.config['SERVER_NAME'] = None

# ---------- НАСТРОЙКИ СЕРВЕРА ----------
SERVER_DIR = 'minecraft_server'
JAR_FILE = 'paper.jar'
JAVA_PATH = 'java'
JAVA_OPTS = ['-Xmx2G', '-Xms1G']
# ---------------------------------------

LOG_MAX_LINES = 2000
log_buffer = deque(maxlen=LOG_MAX_LINES)
server_process = None
stop_requested = False

# ---------- ПОТОК ЧТЕНИЯ ЛОГОВ ----------
def read_output(proc):
    global log_buffer, server_process, stop_requested
    try:
        for line in iter(proc.stdout.readline, ''):
            if line:
                log_buffer.append(line.rstrip('\n'))
            else:
                break
    except Exception:
        pass
    finally:
        proc.stdout.close()
        proc.wait()
        server_process = None
        stop_requested = False
        log_buffer.append('[СИСТЕМА] Сервер остановлен.')

def start_server():
    global server_process, stop_requested
    if server_process is not None and server_process.poll() is None:
        return False, 'Сервер уже запущен.'
    jar_path = os.path.join(SERVER_DIR, JAR_FILE)
    if not os.path.exists(jar_path):
        return False, f'Не найден {jar_path}'
    cmd = [JAVA_PATH] + JAVA_OPTS + ['-jar', JAR_FILE, 'nogui']
    try:
        server_process = subprocess.Popen(
            cmd,
            cwd=SERVER_DIR,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
    except Exception as e:
        return False, f'Ошибка запуска: {e}'
    stop_requested = False
    log_buffer.append('[СИСТЕМА] Сервер запускается...')
    threading.Thread(target=read_output, args=(server_process,), daemon=True).start()
    return True, 'Сервер успешно запущен.'

def stop_server():
    global server_process, stop_requested
    if server_process is None or server_process.poll() is not None:
        return False, 'Сервер не запущен.'
    if stop_requested:
        return False, 'Остановка уже инициирована.'
    stop_requested = True
    try:
        server_process.stdin.write('stop\n')
        server_process.stdin.flush()
    except Exception:
        pass
    for _ in range(60):
        if server_process is None or server_process.poll() is not None:
            return True, 'Сервер остановлен.'
        time.sleep(0.5)
    try:
        server_process.terminate()
        server_process.wait(timeout=10)
    except Exception:
        try:
            server_process.kill()
        except Exception:
            pass
    server_process = None
    stop_requested = False
    log_buffer.append('[СИСТЕМА] Сервер принудительно остановлен.')
    return True, 'Сервер остановлен принудительно.'

# ---------- БЕЗОПАСНАЯ ПРОВЕРКА ПУТИ ----------
def get_safe_path(relative_path):
    """Возвращает абсолютный путь, если он внутри SERVER_DIR, иначе None."""
    abs_server = os.path.abspath(SERVER_DIR)
    abs_path = os.path.normpath(os.path.join(abs_server, relative_path))
    if not abs_path.startswith(abs_server):
        return None
    return abs_path

# ---------- ДЕКОРАТОР АВТОРИЗАЦИИ ----------
def login_required(f):
    def wrapper(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

# ---------- МАРШРУТЫ ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ''
    if request.method == 'POST':
        if request.form.get('username') == 'Олег' and request.form.get('password') == '5464475337745':
            session['logged_in'] = True
            return redirect(url_for('index'))
        error = 'Неверное имя пользователя или пароль'
    return render_template_string(LOGIN_TEMPLATE, error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    running = server_process is not None and server_process.poll() is None
    return render_template_string(INDEX_TEMPLATE, running=running)

@app.route('/start', methods=['POST'])
@login_required
def start():
    ok, msg = start_server()
    return jsonify({'success': ok, 'message': msg})

@app.route('/stop', methods=['POST'])
@login_required
def stop():
    ok, msg = stop_server()
    return jsonify({'success': ok, 'message': msg})

@app.route('/console')
@login_required
def console():
    running = server_process is not None and server_process.poll() is None
    return render_template_string(CONSOLE_TEMPLATE, running=running)

@app.route('/console/log')
@login_required
def console_log():
    lines = list(log_buffer)[-200:]
    running = server_process is not None and server_process.poll() is None
    return jsonify({'lines': lines, 'running': running})

@app.route('/console/command', methods=['POST'])
@login_required
def send_command():
    if server_process is None or server_process.poll() is not None:
        return jsonify({'success': False, 'message': 'Сервер не запущен'})
    cmd = request.form.get('command', '').strip()
    if not cmd:
        return jsonify({'success': False, 'message': 'Пустая команда'})
    try:
        server_process.stdin.write(cmd + '\n')
        server_process.stdin.flush()
    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {e}'})
    return jsonify({'success': True})

@app.route('/plugins')
@login_required
def plugins():
    plugins_dir = os.path.join(SERVER_DIR, 'plugins')
    os.makedirs(plugins_dir, exist_ok=True)
    plugin_files = [f for f in os.listdir(plugins_dir) if f.endswith('.jar')]
    plugin_files.sort()
    running = server_process is not None and server_process.poll() is None
    return render_template_string(PLUGINS_TEMPLATE, plugins=plugin_files, running=running)

@app.route('/plugins/upload', methods=['POST'])
@login_required
def upload_plugin():
    if 'file' not in request.files:
        return redirect(url_for('plugins'))
    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.jar'):
        return redirect(url_for('plugins'))
    filename = secure_filename(file.filename)
    plugins_dir = os.path.join(SERVER_DIR, 'plugins')
    os.makedirs(plugins_dir, exist_ok=True)
    file.save(os.path.join(plugins_dir, filename))
    return redirect(url_for('plugins'))

@app.route('/plugins/download', methods=['POST'])
@login_required
def download_plugin():
    url = request.form.get('url', '').strip()
    if not url:
        return redirect(url_for('plugins'))
    filename = request.form.get('filename', '').strip()
    if not filename:
        parsed = urlparse(url)
        filename = os.path.basename(unquote(parsed.path))
    if not filename or not filename.endswith('.jar'):
        filename = 'downloaded_plugin.jar'
    plugins_dir = os.path.join(SERVER_DIR, 'plugins')
    os.makedirs(plugins_dir, exist_ok=True)
    dest = os.path.join(plugins_dir, secure_filename(filename))
    try:
        r = requests.get(url, stream=True, timeout=30)
        r.raise_for_status()
        with open(dest, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    except Exception as e:
        print(f'Ошибка загрузки: {e}')
    return redirect(url_for('plugins'))

@app.route('/plugins/delete/<name>', methods=['POST'])
@login_required
def delete_plugin(name):
    plugins_dir = os.path.join(SERVER_DIR, 'plugins')
    safe = secure_filename(name)
    path = os.path.join(plugins_dir, safe)
    if os.path.exists(path) and safe.endswith('.jar'):
        os.remove(path)
    return redirect(url_for('plugins'))

# ---------- ФАЙЛОВЫЙ МЕНЕДЖЕР ----------
@app.route('/files')
@login_required
def files():
    # текущий относительный путь
    rel_path = request.args.get('path', '')
    abs_path = get_safe_path(rel_path)
    if abs_path is None:
        abort(403)  # попытка выйти за пределы
    if not os.path.exists(abs_path):
        abort(404)
    if not os.path.isdir(abs_path):
        abort(400)  # это файл, а не папка

    items = []
    try:
        for name in os.listdir(abs_path):
            full = os.path.join(abs_path, name)
            is_dir = os.path.isdir(full)
            items.append({
                'name': name,
                'is_dir': is_dir,
                'size': os.path.getsize(full) if not is_dir else 0,
                'mtime': os.path.getmtime(full)
            })
    except PermissionError:
        abort(403)

    items.sort(key=lambda x: (not x['is_dir'], x['name'].lower()))
    parent = os.path.dirname(rel_path) if rel_path else None
    running = server_process is not None and server_process.poll() is None
    return render_template_string(FILES_TEMPLATE,
                                  items=items,
                                  current_path=rel_path,
                                  parent_path=parent,
                                  running=running)

@app.route('/files/view')
@login_required
def view_file():
    rel_path = request.args.get('path', '')
    abs_path = get_safe_path(rel_path)
    if abs_path is None or not os.path.isfile(abs_path):
        abort(404)
    # Ограничение на размер для просмотра (1 МБ)
    if os.path.getsize(abs_path) > 1_000_000:
        return render_template_string(ERROR_TEMPLATE, message='Файл слишком большой для просмотра (более 1 МБ).')
    try:
        with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        content = f'Ошибка чтения: {e}'
    running = server_process is not None and server_process.poll() is None
    return render_template_string(VIEW_TEMPLATE,
                                  content=content,
                                  filename=os.path.basename(abs_path),
                                  path=rel_path,
                                  running=running)

@app.route('/files/edit', methods=['GET', 'POST'])
@login_required
def edit_file():
    rel_path = request.args.get('path', '')
    abs_path = get_safe_path(rel_path)
    if abs_path is None or not os.path.isfile(abs_path):
        abort(404)
    if os.path.getsize(abs_path) > 1_000_000:
        return render_template_string(ERROR_TEMPLATE, message='Файл слишком большой для редактирования (более 1 МБ).')

    if request.method == 'POST':
        content = request.form.get('content', '')
        try:
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return redirect(url_for('files', path=os.path.dirname(rel_path)))
        except Exception as e:
            return render_template_string(ERROR_TEMPLATE, message=f'Ошибка сохранения: {e}')

    try:
        with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
    except Exception as e:
        content = f'Ошибка чтения: {e}'
    running = server_process is not None and server_process.poll() is None
    return render_template_string(EDIT_TEMPLATE,
                                  content=content,
                                  filename=os.path.basename(abs_path),
                                  path=rel_path,
                                  running=running)

@app.route('/files/delete', methods=['POST'])
@login_required
def delete_file():
    rel_path = request.form.get('path', '')
    abs_path = get_safe_path(rel_path)
    if abs_path is None:
        abort(403)
    if not os.path.exists(abs_path):
        abort(404)
    try:
        if os.path.isdir(abs_path):
            shutil.rmtree(abs_path)
        else:
            os.remove(abs_path)
    except Exception as e:
        return render_template_string(ERROR_TEMPLATE, message=f'Ошибка удаления: {e}')
    parent = os.path.dirname(rel_path)
    return redirect(url_for('files', path=parent))

# ---------- HTML-ШАБЛОНЫ ----------
LOGIN_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Вход</title><meta charset="utf-8">
<style>
body { font-family: sans-serif; background: #2c3e50; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
.login-box { background: #ecf0f1; padding: 30px; border-radius: 10px; box-shadow: 0 0 20px rgba(0,0,0,0.4); text-align: center; }
input { display: block; width: 250px; margin: 10px auto; padding: 10px; border-radius: 5px; border: 1px solid #bdc3c7; }
button { background: #27ae60; color: white; border: none; padding: 10px 30px; border-radius: 5px; cursor: pointer; font-size: 16px; }
.error { color: red; margin-top: 10px; }
</style></head>
<body>
<div class="login-box">
<h2>Управление сервером</h2>
<form method="post">
<input type="text" name="username" placeholder="Логин" required>
<input type="password" name="password" placeholder="Пароль" required>
<button type="submit">Войти</button>
</form>
{% if error %}<div class="error">{{ error }}</div>{% endif %}
</div>
</body>
</html>
'''

INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Панель управления</title><meta charset="utf-8">
<style>
body { font-family: sans-serif; background: #34495e; color: white; padding: 20px; }
a { color: #1abc9c; }
.status { font-size: 1.5em; margin: 20px 0; }
.btn { padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin-right: 10px; }
.btn-start { background: #27ae60; color: white; }
.btn-stop { background: #e74c3c; color: white; }
.nav { margin-bottom: 30px; }
.nav a { margin-right: 15px; text-decoration: none; background: #2c3e50; padding: 8px 15px; border-radius: 5px; }
.message { margin-top: 15px; color: #f1c40f; }
</style></head>
<body>
<div class="nav">
<a href="{{ url_for('index') }}">Главная</a>
<a href="{{ url_for('console') }}">Консоль</a>
<a href="{{ url_for('plugins') }}">Плагины</a>
<a href="{{ url_for('files') }}">Файлы</a>
<a href="{{ url_for('logout') }}" style="float:right; background:#c0392b;">Выйти</a>
</div>
<h1>Управление сервером Minecraft (Paper 1.21.7)</h1>
<div class="status">Статус: <strong id="status-text">{{ "Запущен" if running else "Остановлен" }}</strong></div>
<div>
{% if running %}
<button class="btn btn-stop" onclick="stopServer()">Остановить сервер</button>
{% else %}
<button class="btn btn-start" onclick="startServer()">Запустить сервер</button>
{% endif %}
</div>
<div id="message" class="message"></div>
<script>
async function startServer() {
    const resp = await fetch('/start', { method: 'POST' });
    const data = await resp.json();
    document.getElementById('message').innerText = data.message;
    if (data.success) location.reload();
}
async function stopServer() {
    const resp = await fetch('/stop', { method: 'POST' });
    const data = await resp.json();
    document.getElementById('message').innerText = data.message;
    if (data.success) location.reload();
}
</script>
</body>
</html>
'''

CONSOLE_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Консоль</title><meta charset="utf-8">
<style>
body { font-family: monospace; background: #1e1e1e; color: #dcdcdc; padding: 20px; }
a { color: #1abc9c; }
.nav a { margin-right: 10px; background: #333; padding: 5px 10px; border-radius: 4px; text-decoration: none; }
#log { background: #111; border: 1px solid #555; width: 100%; height: 70vh; overflow-y: scroll; padding: 10px; white-space: pre-wrap; }
.input-area { margin-top: 10px; display: flex; }
.input-area input { flex: 1; padding: 8px; background: #333; color: white; border: 1px solid #777; }
.input-area button { padding: 8px 20px; margin-left: 5px; background: #2980b9; color: white; border: none; cursor: pointer; }
</style></head>
<body>
<div class="nav">
<a href="{{ url_for('index') }}">Главная</a>
<a href="{{ url_for('console') }}">Консоль</a>
<a href="{{ url_for('plugins') }}">Плагины</a>
<a href="{{ url_for('files') }}">Файлы</a>
<a href="{{ url_for('logout') }}" style="float:right; background:#c0392b;">Выйти</a>
</div>
<h2>Консоль сервера</h2>
<div id="log"></div>
<div class="input-area">
<input type="text" id="command" placeholder="Введите команду...">
<button onclick="sendCommand()">Отправить</button>
</div>
<script>
const logDiv = document.getElementById('log');
async function updateLog() {
    try {
        const resp = await fetch('/console/log');
        const data = await resp.json();
        logDiv.textContent = data.lines.join('\\n');
        logDiv.scrollTop = logDiv.scrollHeight;
    } catch(e) {}
}
async function sendCommand() {
    const cmd = document.getElementById('command').value;
    if (!cmd) return;
    await fetch('/console/command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: 'command=' + encodeURIComponent(cmd)
    });
    document.getElementById('command').value = '';
}
setInterval(updateLog, 800);
updateLog();
document.getElementById('command').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') sendCommand();
});
</script>
</body>
</html>
'''

PLUGINS_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Плагины</title><meta charset="utf-8">
<style>
body { font-family: sans-serif; background: #2c3e50; color: white; padding: 20px; }
a { color: #1abc9c; }
.nav a { margin-right: 10px; background: #34495e; padding: 5px 10px; border-radius: 4px; text-decoration: none; }
.plugin-list { list-style: none; padding: 0; }
.plugin-list li { background: #34495e; margin: 5px 0; padding: 10px; border-radius: 6px; display: flex; justify-content: space-between; align-items: center; }
.section { background: #1a252f; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
button { background: #e74c3c; border: none; color: white; padding: 5px 10px; border-radius: 4px; cursor: pointer; }
.upload-btn { background: #27ae60; }
input[type="text"], input[type="file"] { padding: 6px; }
</style></head>
<body>
<div class="nav">
<a href="{{ url_for('index') }}">Главная</a>
<a href="{{ url_for('console') }}">Консоль</a>
<a href="{{ url_for('plugins') }}">Плагины</a>
<a href="{{ url_for('files') }}">Файлы</a>
<a href="{{ url_for('logout') }}" style="float:right; background:#c0392b;">Выйти</a>
</div>
<h1>Управление плагинами</h1>
<div class="section">
<h3>Загрузить плагин с компьютера</h3>
<form action="{{ url_for('upload_plugin') }}" method="post" enctype="multipart/form-data">
<input type="file" name="file" accept=".jar" required>
<button type="submit" class="upload-btn">Загрузить</button>
</form>
</div>
<div class="section">
<h3>Скачать плагин по ссылке</h3>
<form action="{{ url_for('download_plugin') }}" method="post">
<input type="text" name="url" placeholder="https://... плагин.jar" style="width:70%" required>
<input type="text" name="filename" placeholder="Имя файла (необязательно)">
<button type="submit">Скачать</button>
</form>
</div>
<h3>Установленные плагины (папка plugins)</h3>
{% if plugins %}
<ul class="plugin-list">
{% for p in plugins %}
<li><span>{{ p }}</span>
<form action="{{ url_for('delete_plugin', name=p) }}" method="post" onsubmit="return confirm('Удалить {{ p }}?');">
<button type="submit">Удалить</button>
</form></li>
{% endfor %}
</ul>
{% else %}
<p>Плагинов не найдено.</p>
{% endif %}
<p style="margin-top:20px;"><i>Перезагрузите сервер после добавления/удаления плагинов (команда <b>reload confirm</b> в консоли).</i></p>
</body>
</html>
'''

FILES_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Файлы сервера</title><meta charset="utf-8">
<style>
body { font-family: sans-serif; background: #2c3e50; color: white; padding: 20px; }
a { color: #1abc9c; }
.nav a { margin-right: 10px; background: #34495e; padding: 5px 10px; border-radius: 4px; text-decoration: none; }
.file-list { list-style: none; padding: 0; }
.file-list li { background: #34495e; margin: 4px 0; padding: 8px 12px; border-radius: 5px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }
.file-list .name a { text-decoration: none; color: #ecf0f1; }
.file-list .size { margin-left: 20px; color: #bdc3c7; font-size: 0.9em; }
.file-list .actions form { display: inline; margin-left: 10px; }
button { background: #e74c3c; border: none; color: white; padding: 4px 8px; border-radius: 3px; cursor: pointer; font-size: 0.9em; }
.edit-btn { background: #2980b9; }
.parent-link { margin-bottom: 15px; display: block; }
</style></head>
<body>
<div class="nav">
<a href="{{ url_for('index') }}">Главная</a>
<a href="{{ url_for('console') }}">Консоль</a>
<a href="{{ url_for('plugins') }}">Плагины</a>
<a href="{{ url_for('files') }}">Файлы</a>
<a href="{{ url_for('logout') }}" style="float:right; background:#c0392b;">Выйти</a>
</div>
<h2>Файлы сервера: /{{ current_path }}</h2>
{% if parent_path is not none %}
<a class="parent-link" href="{{ url_for('files', path=parent_path) }}">⬆ На уровень выше</a>
{% else %}
<a class="parent-link" href="{{ url_for('files') }}">⬆ Корень сервера</a>
{% endif %}
<ul class="file-list">
{% for item in items %}
<li>
<span class="name">
{% if item.is_dir %}
📁 <a href="{{ url_for('files', path=(current_path + '/' + item.name).lstrip('/')) }}">{{ item.name }}/</a>
{% else %}
📄 {{ item.name }}
{% endif %}
</span>
<span class="size">{{ "%.1f KB"|format(item.size/1024) if not item.is_dir else '' }}</span>
<span class="actions">
{% if not item.is_dir %}
<a href="{{ url_for('view_file', path=(current_path + '/' + item.name).lstrip('/')) }}"><button class="edit-btn" type="button">👁 Смотреть</button></a>
<a href="{{ url_for('edit_file', path=(current_path + '/' + item.name).lstrip('/')) }}"><button class="edit-btn" type="button">✏️ Редактировать</button></a>
{% endif %}
<form method="post" action="{{ url_for('delete_file') }}" onsubmit="return confirm('Удалить {{ item.name }}?');">
<input type="hidden" name="path" value="{{ (current_path + '/' + item.name).lstrip('/') }}">
<button type="submit">🗑 Удалить</button>
</form>
</span>
</li>
{% endfor %}
</ul>
</body>
</html>
'''

VIEW_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Просмотр: {{ filename }}</title><meta charset="utf-8">
<style>
body { font-family: monospace; background: #1e1e1e; color: #dcdcdc; padding: 20px; }
a { color: #1abc9c; }
.nav a { margin-right: 10px; background: #333; padding: 5px 10px; border-radius: 4px; text-decoration: none; }
pre { background: #111; border: 1px solid #555; padding: 15px; overflow: auto; max-height: 80vh; white-space: pre-wrap; word-wrap: break-word; }
</style></head>
<body>
<div class="nav">
<a href="{{ url_for('index') }}">Главная</a>
<a href="{{ url_for('files', path=parent) }}">← Назад к файлам</a>
<a href="{{ url_for('edit_file', path=path) }}">✏️ Редактировать</a>
<a href="{{ url_for('logout') }}" style="float:right; background:#c0392b;">Выйти</a>
</div>
<h2>Просмотр: {{ filename }}</h2>
<pre>{{ content }}</pre>
</body>
</html>
'''

EDIT_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Редактирование: {{ filename }}</title><meta charset="utf-8">
<style>
body { font-family: monospace; background: #1e1e1e; color: #dcdcdc; padding: 20px; }
a { color: #1abc9c; }
.nav a { margin-right: 10px; background: #333; padding: 5px 10px; border-radius: 4px; text-decoration: none; }
textarea { width: 100%; height: 70vh; background: #111; color: #dcdcdc; border: 1px solid #555; padding: 10px; font-family: monospace; resize: vertical; }
button { padding: 10px 25px; background: #27ae60; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 1em; margin-top: 10px; }
</style></head>
<body>
<div class="nav">
<a href="{{ url_for('index') }}">Главная</a>
<a href="{{ url_for('files', path=parent) }}">← Назад к файлам</a>
<a href="{{ url_for('logout') }}" style="float:right; background:#c0392b;">Выйти</a>
</div>
<h2>Редактирование: {{ filename }}</h2>
<form method="post">
<textarea name="content">{{ content }}</textarea>
<button type="submit">💾 Сохранить</button>
</form>
</body>
</html>
'''

ERROR_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head><title>Ошибка</title><meta charset="utf-8">
<style>
body { font-family: sans-serif; background: #c0392b; color: white; padding: 30px; text-align: center; }
a { color: #f1c40f; }
</style></head>
<body>
<h1>⚠️ Ошибка</h1>
<p>{{ message }}</p>
<a href="javascript:history.back()">← Назад</a>
</body>
</html>
'''

if __name__ == '__main__':
    os.makedirs(SERVER_DIR, exist_ok=True)
    app.run(debug=False, host='0.0.0.0', port=5000)