import time
import paho.mqtt.client as mqtt
from supabase import create_client

# --- CONFIGURAÇÕES ---
SUPABASE_URL = "https://skvrfxnvbjtqzhcbeits.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNrdnJmeG52Ymp0cXpoY2JlaXRzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc1MzA0NTcsImV4cCI6MjA5MzEwNjQ1N30._D7ue2nNBeeVOknbbVMmwNi5cUNYEJvj0MRbmjjl0sQ"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

MQTT_BROKER = "79cfe6e1598b447b95c57a4303744c21.s1.eu.hivemq.cloud"
MQTT_USER = "ROVER-1"
MQTT_PASS = "Rover1grid"

# Dicionário para controlar o tempo de envio de cada sensor
# Formato: {"MQ2": timestamp, "Distancia": timestamp}
ultimos_envios = {}
INTERVALO_ENVIO = 120  # 2 minutos em segundos

def guardar_no_supabase(sensor, valor_bruto):
    agora = time.time()
    
    # Verifica se já passaram 2 minutos desde o último envio DESTE sensor
    if sensor in ultimos_envios:
        tempo_passado = agora - ultimos_envios[sensor]
        if tempo_passado < INTERVALO_ENVIO:
            # Ainda não passaram 2 minutos, ignoramos a gravação
            return

    try:
        try:
            valor_num = float(valor_bruto)
            mensagem_txt = f"Leitura de {sensor}"
        except ValueError:
            valor_num = 0.0
            mensagem_txt = valor_bruto 

        data = {
            "categoria": "SENSOR",
            "origem": sensor,
            "valor": valor_num,
            "mensagem": mensagem_txt,
            "nivel_alerta": 0
        }
        
        supabase.table("logs_operacao").insert(data).execute()
        
        # Atualiza o cronómetro para este sensor
        ultimos_envios[sensor] = agora
        print(f"✅ GRAVADO (2min): {sensor} -> {valor_bruto}")
        
    except Exception as e:
        print(f"❌ Erro ao guardar: {e}")

def on_message(client, userdata, msg):
    try:
        valor = msg.payload.decode()
        topico = msg.topic
        sensor_nome = topico.split('/')[-1]
        
        # O script continua a receber tudo em tempo real no terminal
        # Mas a função guardar_no_supabase decide se grava ou não
        guardar_no_supabase(sensor_nome, valor)
    except:
        pass

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(MQTT_USER, MQTT_PASS)
client.tls_set() 
client.on_message = on_message

print("Bridge Ativa! (Intervalo: 2 min)")
client.connect(MQTT_BROKER, 8883)
client.subscribe("G.R.I.D/#") 
client.loop_forever()