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


# ── Verificação de código de vinculação de rover ─────────────────────────────
from flask import request, jsonify as _jsonify
from core import supabase as _supabase


def rover_verificar_codigo():
    """
    Valida o código enviado por email.
    Consulta rovers pela coluna email_dono + ativo=False.
    Após validação: ativo=True, users.rover_id = rovers.id.
    """
    email  = request.form.get('email', '').strip().lower()
    codigo = request.form.get('codigo', '').strip()

    if not email or not codigo:
        return _jsonify({'status': 'error', 'message': 'Dados em falta.'}), 400

    try:
        rv = _supabase.table('rovers').select('id, codigo, nome') \
            .eq('email_dono', email).eq('ativo', False).limit(1).execute()

        if not rv.data:
            return _jsonify({'status': 'error', 'message': 'Nenhum rover pendente para este email.'})

        rv_data = rv.data[0]

        if str(rv_data['codigo']).strip() != codigo:
            return _jsonify({'status': 'error', 'message': 'Código inválido. Verifica o email.'})

        rover_id = rv_data['id']

        # Marcar rover como ativo
        _supabase.table('rovers').update({'ativo': True}).eq('id', rover_id).execute()

        # Ligar rover ao utilizador via rover_id (FK int8)
        _supabase.table('users').update({'rover_id': rover_id}).eq('email', email).execute()

        return _jsonify({'status': 'success', 'rover_nome': rv_data['nome']})
    except Exception as e:
        import traceback
        print(f'[ROVER VERIFY] {e}')
        traceback.print_exc()
        return _jsonify({'status': 'error', 'message': 'Erro interno.'}), 500