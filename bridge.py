import os
import time
import paho.mqtt.client as mqtt
from dotenv import load_dotenv
from supabase import create_client
 
load_dotenv()
 
# --- CONFIGURAÇÕES 
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase     = create_client(SUPABASE_URL, SUPABASE_KEY)
 
MQTT_BROKER = os.getenv('MQTT_BROKER', "79cfe6e1598b447b95c57a4303744c21.s1.eu.hivemq.cloud")
MQTT_USER   = os.getenv('MQTT_USER', "ROVER-1")
MQTT_PASS   = os.getenv('MQTT_PASS', "Rover1grid")
 
ultimos_envios  = {}
INTERVALO_ENVIO = 120  # 2 minutos
 
def guardar_no_supabase(sensor, valor_bruto):
    agora = time.time()
    if sensor in ultimos_envios and (agora - ultimos_envios[sensor]) < INTERVALO_ENVIO:
        return
    try:
        try:
            valor_num    = float(valor_bruto)
            mensagem_txt = f"Leitura de {sensor}"
        except ValueError:
            valor_num    = 0.0
            mensagem_txt = valor_bruto
 
        data = {
            "categoria":    "SENSOR",
            "origem":       sensor,
            "valor":        valor_num,
            "mensagem":     mensagem_txt,
            "nivel_alerta": 0
        }
 
        supabase.table("logs_operacao").insert(data).execute()
        ultimos_envios[sensor] = agora
        print(f"✅ GRAVADO (2min): {sensor} -> {valor_bruto}")
 
    except Exception as e:
        print(f" Erro ao guardar: {e}")
 
def on_message(client, userdata, msg):
    try:
        valor       = msg.payload.decode()
        sensor_nome = msg.topic.split('/')[-1]
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