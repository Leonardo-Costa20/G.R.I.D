import json
import core
from flask import jsonify

socketio = core.socketio


@socketio.on('drive_command')
def handle_drive_command(data):
    command = str(data.get('command', '')).strip().lower()
    try:
        speed = int(data.get('speed', 0))
    except Exception:
        speed = 0

    if command not in ['forward', 'backward', 'left', 'right', 'stop', 'forward-left', 'forward-right', 'backward-left', 'backward-right']:
        return {'status': 'error', 'message': 'invalid_command'}

    speed = max(0, min(100, speed))
    payload = json.dumps({'command': command, 'speed': speed})
    topic = 'G.R.I.D/drive/command'

    if core.mqtt_client:
        try:
            core.mqtt_client.publish(topic, payload, qos=1)
            return {'status': 'ok', 'topic': topic, 'payload': payload}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    return {'status': 'error', 'message': 'mqtt_unavailable'}


@socketio.on('connect')
def on_connect():
    core.clientes_conectados_ws += 1
    core.socketio.emit('rover_status_update', {'status': 'online' if core.rover_online_com_certeza else 'offline'})


@socketio.on('disconnect')
def on_disconnect():
    if core.clientes_conectados_ws > 0:
        core.clientes_conectados_ws -= 1
