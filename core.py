import os
import time
import threading
import secrets
import requests
from datetime import datetime, timezone
import json
import bcrypt
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from supabase import create_client, Client
from flask_socketio import SocketIO

load_dotenv()

SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'grid_secret_key_123')

socketio = SocketIO(cors_allowed_origins="*", async_mode='gevent')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

RESEND_API_KEY = os.getenv('RESEND_API_KEY')
MAILERLITE_API_KEY = os.getenv('MAILERLITE_API_KEY')

MQTT_BROKER = "79cfe6e1598b447b95c57a4303744c21.s1.eu.hivemq.cloud"
MQTT_USER = "ROVER-1"
MQTT_PASS = "Rover1grid"

mqtt_client = None

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


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def check_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def _enviar_email_mailerlite(destinatario: str, assunto: str, html: str) -> bool:
    """Envia email via MailerLite API em background."""
    def _send():
        try:
            resp = requests.post(
                'https://connect.mailerlite.com/api/emails',
                headers={
                    'Authorization': f'Bearer {MAILERLITE_API_KEY}',
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                json={
                    'from':     {'email': 'noreply@grid-os.com', 'name': 'G.R.I.D OS'},
                    'to':       [{'email': destinatario}],
                    'subject':  assunto,
                    'html':     html,
                },
                timeout=10
            )
            if resp.status_code in (200, 201):
                print(f"[EMAIL] Enviado para {destinatario}")
            else:
                print(f"[EMAIL] Erro MailerLite {resp.status_code}: {resp.text}")
        except Exception as e:
            print(f"[EMAIL] Erro ao enviar: {e}")
    threading.Thread(target=_send, daemon=True).start()
    return True


def enviar_email_reset(destinatario: str, codigo: str) -> bool:
    """Envia o email de recuperação via MailerLite."""
    codigo_formatado = f"{codigo[:3]} {codigo[3:]}"
    html = f"""
    <div style="background:#0a0c10;padding:40px;font-family:monospace;color:#c9d1d9;">
        <h1 style="color:#3ecf8e;letter-spacing:4px;font-size:20px;">G.R.I.D OS</h1>
        <p style="color:#6b7280;font-size:11px;letter-spacing:2px;text-transform:uppercase;">Recuperação de Acesso</p>
        <hr style="border-color:#30363d;margin:24px 0;">
        <p>Recebemos um pedido para redefinir a tua password.</p>
        <p>Insere o código abaixo na aplicação. Expira em <strong style="color:#3ecf8e;">15 minutos</strong>.</p>
        <div style="margin:32px 0;text-align:center;">
            <div style="display:inline-block;background:#12151a;border:2px solid #3ecf8e;border-radius:16px;padding:24px 40px;">
                <p style="color:#6b7280;font-size:10px;letter-spacing:3px;text-transform:uppercase;margin:0 0 12px 0;">Código de Verificação</p>
                <p style="color:#3ecf8e;font-size:36px;font-weight:800;letter-spacing:12px;margin:0;">{codigo_formatado}</p>
            </div>
        </div>
        <p style="color:#6b7280;font-size:10px;">Se não pediste isto, ignora este email. A tua conta continua segura.</p>
        <hr style="border-color:#30363d;margin:24px 0;">
        <p style="color:#374151;font-size:9px;letter-spacing:2px;">G.R.I.D OS · PAP 2026</p>
    </div>
    """
    return _enviar_email_mailerlite(destinatario, 'G.R.I.D OS — Código de Recuperação', html)


def inicializar_contador_logs():
    """Procura o número inicial de logs apenas uma vez no arranque do servidor."""
    global total_logs_supabase
    if supabase:
        try:
            res = supabase.table("logs_operacao").select("id", count="exact").limit(1).execute()
            if res.count is not None:
                total_logs_supabase = res.count
        except Exception:
            pass


def monitor_infraestrutura_loop():
    """Thread contínua que envia a velocidade e latências a cada 2 segundos."""
    global rover_online_com_certeza, latencia_db
    while True:
        time.sleep(2)

        if supabase:
            try:
                inicio_ping = time.time()
                supabase.auth.get_session()
                latencia_db = int((time.time() - inicio_ping) * 1000)
            except Exception:
                latencia_db = "FAIL"

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

        valor_limpo = valor.replace('\n', '').replace('\r', '').strip()
        if not valor_limpo:
            return

        try:
            num_valor = float(valor_limpo)
        except ValueError:
            return

        socketio.emit('mqtt_data', {'sensor': sensor_nome, 'valor': valor_limpo})

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
                except Exception:
                    pass

            threading.Thread(target=save_async, args=(data,), daemon=True).start()

        duracao = (time.time() - inicio_processamento) * 1000
        latencia_comunicacao_rover = int(duracao) if duracao > 0 else 24

    except Exception:
        pass


def initialize_mqtt():
    global mqtt_client
    if mqtt_client is not None:
        return

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