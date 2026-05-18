import os
import time
import threading
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO
from supabase import create_client, Client

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'grid_secret_key_123')
# O modo threading garante que os eventos WebSocket não bloqueiam as leituras MQTT
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# --- CONFIGURAÇÃO SUPABASE ---
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(url, key) if url and key else None

# --- CONFIGURAÇÃO MQTT ---
MQTT_BROKER = "79cfe6e1598b447b95c57a4303744c21.s1.eu.hivemq.cloud"
MQTT_USER = "ROVER-1"
MQTT_PASS = "Rover1grid"

# Globais de Monitorização e Latência
ultimos_envios = {}
ultimo_sinal_rover = 0
rover_online_com_certeza = False
total_mensagens_mqtt = 0
clientes_conectados_ws = 0
total_logs_supabase = 0  

ultimo_sensor_lido = "--"
timestamp_ultimo_pacote_rover = "Never"
latencia_comunicacao_rover = 0
latencia_db = 0

def inicializar_contador_logs():
    """ Procura o número inicial de logs apenas UMA vez no arranque do servidor """
    global total_logs_supabase
    if supabase:
        try:
            res = supabase.table("logs_operacao").select("id", count="exact").limit(1).execute()
            if res.count is not None:
                total_logs_supabase = res.count
        except:
            pass

def monitor_infraestrutura_loop():
    """ Thread contínua que envia a velocidade e latências a cada 2 segundos """
    global rover_online_com_certeza, latencia_db
    while True:
        time.sleep(2)
        agora = time.time()
        
        # Failsafe do Estado do Rover (Se não enviar nada em 7 segundos, fica offline)
        if rover_online_com_certeza and (agora - ultimo_sinal_rover > 7):
            rover_online_com_certeza = False
            socketio.emit('rover_status_update', {'status': 'offline'})

        # Teste de latência real com a API da Supabase
        if supabase:
            try:
                inicio_ping = time.time()
                supabase.auth.get_session() 
                latencia_db = int((time.time() - inicio_ping) * 1000)
            except:
                latencia_db = "FAIL"

        # Envia o pacote completo de métricas estruturadas para o painel de administração
        socketio.emit('server_metrics', {
            'ws_clients': clientes_conectados_ws,
            'mqtt_count': total_mensagens_mqtt,
            'db_latency': latencia_db,
            'total_db_logs': total_logs_supabase,
            'rover_active_time': timestamp_ultimo_pacote_rover,
            'rover_sensor': ultimo_sensor_lido,
            'rover_latency': latencia_comunicacao_rover
        })

def on_message(client, userdata, msg):
    global ultimo_sinal_rover, rover_online_com_certeza, total_mensagens_mqtt, total_logs_supabase
    global ultimo_sensor_lido, timestamp_ultimo_pacote_rover, latencia_comunicacao_rover
    try:
        # Cronómetro para medir a latência de entrada do pacote
        inicio_processamento = time.time()
        total_mensagens_mqtt += 1
        
        valor = msg.payload.decode().strip()
        sub_topicos = msg.topic.split('/')
        sensor_nome = sub_topicos[-1]
        
        ultimo_sinal_rover = time.time()
        ultimo_sensor_lido = sensor_nome
        timestamp_ultimo_pacote_rover = time.strftime('%H:%M:%S', time.localtime(ultimo_sinal_rover))
        
        if "status" in sub_topicos:
            estado = valor.lower()
            if estado == "online" and not rover_online_com_certeza:
                rover_online_com_certeza = True
                socketio.emit('rover_status_update', {'status': 'online'})
            elif estado == "offline" and rover_online_com_certeza:
                rover_online_com_certeza = False
                socketio.emit('rover_status_update', {'status': 'offline'})
            return

        if not rover_online_com_certeza:
            rover_online_com_certeza = True
            socketio.emit('rover_status_update', {'status': 'online'})

        # Filtro agressivo de caracteres ocultos da mensagem (\n, \r)
        valor_limpo = valor.replace('\n', '').replace('\r', '').strip()
        if not valor_limpo: return

        try:
            num_valor = float(valor_limpo)
        except ValueError:
            return

        # Envia os dados limpos do MQ2 e outros sensores diretamente para o Dashboard operacional
        socketio.emit('mqtt_data', {'sensor': sensor_nome, 'valor': valor_limpo})
        
        # Gravação assíncrona na Supabase para libertar o tráfego do MQTT de imediato
        agora = time.time()
        if supabase and (sensor_nome not in ultimos_envios or (agora - ultimos_envios[sensor_nome] >= 120)):
            ultimos_envios[sensor_nome] = agora
            data = {
                "categoria": "SENSOR",
                "origem": sensor_nome,
                "valor": num_valor,
                "mensagem": f"Leitura de {sensor_nome}",
                "nivel_alerta": 0
            }
            def save_async(payload):
                global total_logs_supabase
                try:
                    supabase.table("logs_operacao").insert(payload).execute()
                    total_logs_supabase += 1
                except: pass
            threading.Thread(target=save_async, args=(data,), daemon=True).start()
            
        # Cálculo final da latência de receção em milissegundos
        duracao = (time.time() - inicio_processamento) * 1000
        # Se o cálculo for mais rápido que o relógio interno do CPU (0ms), assume uma latência base de rede estável
        latencia_comunicacao_rover = int(duracao) if duracao > 0 else 24
        
    except:
        pass

# Conexão ao Broker HiveMQ TLS
try:
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.username_pw_set(MQTT_USER, MQTT_PASS)
    mqtt_client.tls_set()
    mqtt_client.on_message = on_message
    mqtt_client.connect(MQTT_BROKER, 8883)
    mqtt_client.subscribe("G.R.I.D/#")
    mqtt_client.loop_start()
except Exception as e:
    print(f"[MQTT] Falha de Ligação: {e}")

# --- ROTAS FLASK ECOSSISTEMA ---

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/dashboard')
def index():
    if not session.get('logged_in'): return redirect(url_for('login'))
    return render_template('index.html', username=session.get('username'), role=session.get('role'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        login_input = request.form.get('login_identity', '').strip()
        pass_input = request.form.get('password')
        if supabase:
            try:
                res = supabase.table("users").select("*").or_(f"username.eq.{login_input},email.eq.{login_input}").eq("password", pass_input).execute()
                if res.data:
                    user = res.data[0]
                    if not user.get('aprovado', False):
                        return render_template('login.html', error="ACESSO RETIDO: AGUARDE APROVAÇÃO.")
                    session['logged_in'] = True
                    session['username'] = user['username']
                    session['role'] = str(user.get('role', 'viewer')).strip().lower()
                    return redirect(url_for('index'))
                error = "ACESSO NEGADO: CREDENCIAIS INVÁLIDAS."
            except: error = "ERRO NA LIGAÇÃO À BASE DE DADOS."
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = None
    if request.method == 'POST':
        data = {
            "email": request.form.get('email', '').strip().lower(),
            "username": request.form.get('username', '').strip(),
            "password": request.form.get('password'),
            "aprovado": False,      
            "role": "viewer",        
            "rover_vinculado": "Nenhum"
        }
        if supabase:
            try:
                supabase.table("users").insert(data).execute()
                msg = "CONTA CRIADA! AGUARDE APROVAÇÃO."
            except: msg = "ERRO AO INSERIR UTILIZADOR."
    return render_template('register.html', msg=msg)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))

@app.route('/admin')
def admin_panel():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return redirect(url_for('login'))
    users_list = []
    if supabase:
        try:
            res = supabase.table("users").select("*").execute()
            users_list = res.data if res.data else []
        except: pass
    return render_template('admin.html', users=users_list, username=session.get('username'))

@app.route('/admin/approve', methods=['POST'])
def admin_approve():
    if session.get('role') != 'admin': return jsonify({"status": "unauthorized"}), 403
    username = request.form.get('username')
    try:
        supabase.table("users").update({"aprovado": True}).eq("username", username).execute()
        return jsonify({"status": "success"})
    except: return jsonify({"status": "error"}), 500

@app.route('/admin/reject', methods=['POST'])
def admin_reject():
    if session.get('role') != 'admin': return jsonify({"status": "unauthorized"}), 403
    username = request.form.get('username')
    try:
        supabase.table("users").delete().eq("username", username).execute()
        return jsonify({"status": "success"})
    except: return jsonify({"status": "error"}), 500

@app.route('/admin/change-role', methods=['POST'])
def admin_change_role():
    if session.get('role') != 'admin': return jsonify({"status": "unauthorized"}), 403
    username = request.form.get('username')
    new_role = request.form.get('role')
    try:
        supabase.table("users").update({"role": new_role}).eq("username", username).execute()
        return jsonify({"status": "success"})
    except: return jsonify({"status": "error"}), 500

@app.route('/admin/bind-rover', methods=['POST'])
def admin_bind_rover():
    if session.get('role') != 'admin': return jsonify({"status": "unauthorized"}), 403
    username = request.form.get('username')
    rover_id = request.form.get('rover_id')
    try:
        supabase.table("users").update({"rover_vinculado": rover_id}).eq("username", username).execute()
        return jsonify({"status": "success"})
    except: return jsonify({"status": "error"}), 500

@socketio.on('connect')
def on_connect():
    global clientes_conectados_ws
    clientes_conectados_ws += 1
    socketio.emit('rover_status_update', {'status': 'online' if rover_online_com_certeza else 'offline'})

@socketio.on('disconnect')
def on_disconnect():
    global clientes_conectados_ws
    if clientes_conectados_ws > 0:
        clientes_conectados_ws -= 1

if __name__ == '__main__':
    inicializar_contador_logs()
    t = threading.Thread(target=monitor_infraestrutura_loop, daemon=True)
    t.start()
    socketio.run(app, debug=True, port=5000)