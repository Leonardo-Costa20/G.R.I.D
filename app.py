import os
import time
import threading
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import bcrypt
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, Response
from flask_socketio import SocketIO
from supabase import create_client, Client

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'grid_secret_key_123')
# O modo --------- garante que os eventos WebSocket não bloqueiam as leituras MQTT
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# --- CONFIGURAÇÃO SUPABASE ---
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(url, key) if url and key else None


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def check_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False

# --- CONFIGURAÇÃO SMTP ---
SMTP_EMAIL    = os.getenv('SMTP_EMAIL')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

def enviar_email_reset(destinatario: str, codigo: str) -> bool:
    """Envia o email de recuperação com código único via Gmail SMTP TLS."""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'G.R.I.D OS — Código de Recuperação'
        msg['From']    = SMTP_EMAIL
        msg['To']      = destinatario

        # Separar o código em grupos de 3 para melhor legibilidade
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
        msg.attach(MIMEText(html, 'html'))

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, destinatario, msg.as_string())
        return True
    except Exception as e:
        print(f"[EMAIL] Erro ao enviar: {e}")
        return False

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


# --- ROTAS DE LOGS DE MISSÃO ---

@app.route('/logs')
def logs_page():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('logs.html', username=session.get('username'), role=session.get('role'))

@app.route('/api/logs')
def api_logs():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 25, type=int)
    sensor_filter = request.args.get('sensor', '', type=str)
    start_date = request.args.get('start', '', type=str)
    end_date = request.args.get('end', '', type=str)
    
    if not supabase:
        return jsonify({"error": "Database unavailable"}), 503
    
    try:
        # Usar data_hora em vez de created_at
        query = supabase.table("logs_operacao").select("*", count="exact")
        
        # Filtro por sensor (origem) - excluir 'mapa'
        if sensor_filter:
            query = query.eq("origem", sensor_filter)
        else:
            # Por defeito, excluir o sensor 'mapa'
            query = query.neq("origem", "mapa")
        
        # Filtro por data - usar data_hora
        if start_date:
            query = query.gte("data_hora", start_date + "T00:00:00")
        if end_date:
            query = query.lte("data_hora", end_date + "T23:59:59")
        
        # Ordenação decrescente - usar data_hora
        query = query.order("data_hora", desc=True)
        
        # Paginação
        offset = (page - 1) * per_page
        res = query.range(offset, offset + per_page - 1).execute()
        
        total = res.count if res.count is not None else len(res.data)
        total_pages = (total + per_page - 1) // per_page if total > 0 else 1
        
        return jsonify({
            "logs": res.data,
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs/sensors')
def api_logs_sensors():
    """Retorna lista única de sensores para os filtros - exclui 'mapa'"""
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    if not supabase:
        return jsonify({"sensors": []}), 503
    
    try:
        res = supabase.table("logs_operacao").select("origem").execute()
        # Filtrar: excluir 'mapa', só sensores reais do rover
        sensors = list(set([
            item['origem'] for item in res.data 
            if item.get('origem') and item['origem'] != 'mapa'
        ]))
        return jsonify({"sensors": sorted(sensors)})
    except:
        return jsonify({"sensors": []}), 500

@app.route('/api/logs/export')
def api_logs_export():
    """Exporta logs para CSV simplificado"""
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    sensor_filter = request.args.get('sensor', '', type=str)
    start_date = request.args.get('start', '', type=str)
    end_date = request.args.get('end', '', type=str)
    
    if not supabase:
        return jsonify({"error": "Database unavailable"}), 503
    
    try:
        query = supabase.table("logs_operacao").select("*").order("data_hora", desc=True)
        
        if sensor_filter:
            query = query.eq("origem", sensor_filter)
        else:
            query = query.neq("origem", "mapa")
            
        if start_date:
            query = query.gte("data_hora", start_date + "T00:00:00")
        if end_date:
            query = query.lte("data_hora", end_date + "T23:59:59")
        
        res = query.limit(1000).execute()
        
        import csv
        import io
        from flask import Response
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header simples
        writer.writerow(['Sensor', 'Valor', 'Hora'])
        
        for log in res.data:
            writer.writerow([
                log.get('origem', 'N/A'),
                log.get('valor', ''),
                log.get('data_hora', '')
            ])
        
        output.seek(0)
        
        from datetime import datetime
        filename = f"GRID_Logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return Response(
            output,
            mimetype="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/csv; charset=utf-8"
            }
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500



#rota de pdf
@app.route('/api/logs/export/pdf')
def api_logs_export_pdf():
    """Exporta logs para PDF formatado"""
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401
    
    sensor_filter = request.args.get('sensor', '', type=str)
    start_date = request.args.get('start', '', type=str)
    end_date = request.args.get('end', '', type=str)
    
    if not supabase:
        return jsonify({"error": "Database unavailable"}), 503
    
    try:
        query = supabase.table("logs_operacao").select("*").order("data_hora", desc=True)
        
        if sensor_filter:
            query = query.eq("origem", sensor_filter)
        else:
            query = query.neq("origem", "mapa")
            
        if start_date:
            query = query.gte("data_hora", start_date + "T00:00:00")
        if end_date:
            query = query.lte("data_hora", end_date + "T23:59:59")
        
        res = query.limit(500).execute()
        
        # Criar PDF em memória
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, 
                              rightMargin=2*cm, leftMargin=2*cm,
                              topMargin=2*cm, bottomMargin=2*cm)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#3ecf8e'),
            spaceAfter=20,
            alignment=1  # Centro
        )
        elements.append(Paragraph("G.R.I.D OS - MISSION LOGS", title_style))
        elements.append(Spacer(1, 0.3*cm))
        
        # Info da missão
        info_style = ParagraphStyle(
            'InfoStyle',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            spaceAfter=5
        )
        now = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
        elements.append(Paragraph(f"<b>Operador:</b> {session.get('username', 'N/A')}", info_style))
        elements.append(Paragraph(f"<b>Gerado em:</b> {now}", info_style))
        elements.append(Paragraph(f"<b>Total de registos:</b> {len(res.data)}", info_style))
        elements.append(Spacer(1, 0.5*cm))
        
        # Dados da tabela
        table_data = [['Sensor', 'Valor', 'Hora']]
        
        unidades = {
            'MQ2': 'ppm',
            'Distancia': 'cm',
            'Acel_X': 'm/s²', 'Acel_Y': 'm/s²', 'Acel_Z': 'm/s²',
            'Gyro_X': '°/s', 'Gyro_Y': '°/s', 'Gyro_Z': '°/s',
            'Temperatura': '°C',
            'Pressao': 'hPa'
        }
        
        for log in res.data:
            origem = log.get('origem', 'N/A')
            valor = log.get('valor', '')
            unidade = unidades.get(origem, '')
            hora = log.get('data_hora', '')[:16]  # Só data e hora, sem segundos
            
            valor_str = f"{valor} {unidade}" if unidade else str(valor)
            table_data.append([origem, valor_str, hora])
        
        # Criar tabela
        table = Table(table_data, colWidths=[6*cm, 4*cm, 5*cm])
        table.setStyle(TableStyle([
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#161b22')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#3ecf8e')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Corpo
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#0d1117')),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.white),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#30363d')),
            ('LINEBELOW', (0, 0), (-1, 0), 1, colors.HexColor('#3ecf8e')),
            
            # Alternar cores de linha
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#0d1117'), colors.HexColor('#161b22')]),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 1*cm))
        
        # Rodapé
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1
        )
        elements.append(Paragraph("G.R.I.D OS | Ground Recon & Intelligent Detection", footer_style))
        
        # Gerar PDF
        doc.build(elements)
        buffer.seek(0)
        
        filename = f"GRID_Mission_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return Response(
            buffer,
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/pdf"
            }
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# --- ROTAS FLASK ECOSSISTEMA ---

@app.route('/')
def landing_apresentacao():
    if session.get('logged_in'):
        return redirect(url_for('index'))
    # Quando aberta como PWA instalada, o Chrome faz um navigate para '/'
    # sem Referer e com Sec-Fetch-Mode: navigate — redirecionar para /app (welcome)
    referer = request.headers.get('Referer', '')
    sec_fetch_site = request.headers.get('Sec-Fetch-Site', '')
    # 'none' = navegação direta (barra de endereço ou PWA launcher)
    if not referer and sec_fetch_site == 'none':
        return redirect(url_for('welcome'))
    return render_template('landing_apresentacao.html')

@app.route('/app')
def welcome():
    if session.get('logged_in'):
        return redirect(url_for('index'))
    return render_template('welcome.html')

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
                res = supabase.table("users").select("*").or_(f"username.eq.{login_input},email.eq.{login_input}").execute()
                if res.data:
                    user = res.data[0]
                    stored_pw = user.get('password', '')

                    # Suporta bcrypt e texto plano (migração automática)
                    if stored_pw.startswith('$2b$') or stored_pw.startswith('$2a$'):
                        pw_ok = check_password(pass_input, stored_pw)
                    else:
                        # Ainda em texto plano: verifica e migra para bcrypt
                        pw_ok = (pass_input == stored_pw)
                        if pw_ok:
                            try:
                                supabase.table("users").update({"password": hash_password(pass_input)}).eq("id", user['id']).execute()
                            except:
                                pass

                    if pw_ok:
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
            "password": hash_password(request.form.get('password', '')),
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
    return redirect(url_for('welcome'))

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
    return render_template('admin.html', users=users_list, username=session.get('username'), role=session.get('role'))

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

from datetime import datetime, timezone

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        try:
            user = supabase.table("users").select("email").eq("email", email).maybe_single().execute()

            if user.data:
                # Gera código numérico de 6 dígitos
                codigo = f"{secrets.randbelow(1000000):06d}"
                created_at = datetime.now(timezone.utc).isoformat()

                # Delete + insert para garantir que o código novo é sempre guardado
                supabase.table("password_resets").delete().eq("email", email).execute()
                supabase.table("password_resets").insert({
                    "email": email,
                    "token": codigo,
                    "created_at": created_at
                }).execute()

                print(f"[RESET] Código gerado para {email}: {codigo}")  # debug temporário
                enviar_email_reset(email, codigo)

        except Exception as e:
            print(f"[FORGOT ERROR] {e}")

        # Redireciona para a página de inserção de código, passando o email (ofuscado na resposta)
        return render_template('forgot_password.html',
                               step='verify',
                               email=email,
                               msg="Se o email existir, receberás o código em breve.",
                               msg_type='success')

    return render_template('forgot_password.html', step='email')


@app.route('/verify-code', methods=['POST'])
def verify_code():
    email = request.form.get('email', '').strip().lower()
    codigo = request.form.get('codigo', '').replace(' ', '').strip()

    error = None
    try:
        res = supabase.table("password_resets").select("*").eq("email", email).maybe_single().execute()

        if res.data:
            created = datetime.fromisoformat(res.data['created_at'].replace('Z', '+00:00'))
            agora = datetime.now(timezone.utc)
            delta = (agora - created).total_seconds()

            if delta > 900:  # 15 minutos
                error = "CÓDIGO EXPIRADO. SOLICITA UM NOVO."
            elif str(res.data['token']).strip() != codigo:
                error = "CÓDIGO INVÁLIDO. TENTA NOVAMENTE."
            else:
                # Código correto — guarda na sessão e redireciona para reset
                session['reset_email'] = email
                session['reset_verified'] = True
                return redirect(url_for('reset_password'))
        else:
            error = "NENHUM PEDIDO ENCONTRADO PARA ESTE EMAIL."

    except Exception as e:
        print(f"[VERIFY ERROR] {e}")
        error = "ERRO AO VERIFICAR O CÓDIGO."

    return render_template('forgot_password.html',
                           step='verify',
                           email=email,
                           error=error)


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    # Garante que só chega aqui quem verificou o código
    if not session.get('reset_verified') or not session.get('reset_email'):
        return redirect(url_for('forgot_password'))

    email = session['reset_email']
    error = None

    if request.method == 'POST':
        nova_pw = request.form.get('password', '')
        confirmar = request.form.get('confirm_password', '')

        if len(nova_pw) < 6:
            error = "A PASSWORD DEVE TER PELO MENOS 6 CARACTERES."
        elif nova_pw != confirmar:
            error = "AS PASSWORDS NÃO COINCIDEM."
        else:
            try:
                supabase.table("users").update({"password": hash_password(nova_pw)}).eq("email", email).execute()
                supabase.table("password_resets").delete().eq("email", email).execute()

                # Limpa sessão de reset
                session.pop('reset_email', None)
                session.pop('reset_verified', None)

                return render_template('login.html', success="PASSWORD ATUALIZADA! FAZ LOGIN.")
            except Exception as e:
                error = "ERRO AO ATUALIZAR A BASE DE DADOS."

    return render_template('reset_password.html', error=error)


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
    
    # O Railway fornece a porta através da variável de ambiente PORT
    port = int(os.environ.get("PORT", 5000))
    
    # O host '0.0.0.0' é essencial para que o servidor seja acessível externamente
    socketio.run(app, host='0.0.0.0', port=port, debug=False)