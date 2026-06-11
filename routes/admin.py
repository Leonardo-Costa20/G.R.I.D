import secrets

from flask import render_template, request, jsonify, redirect, url_for, session
from core import supabase, _enviar_email_mailerlite


def _enviar_email_rover(destinatario: str, nome_rover: str, codigo: str) -> bool:
    """Envia email de vinculação de rover via MailerLite."""
    codigo_fmt = f"{codigo[:3]} {codigo[3:]}"
    html = f"""
    <div style="background:#0a0c10;padding:40px;font-family:monospace;color:#c9d1d9;">
        <h1 style="color:#3ecf8e;letter-spacing:4px;font-size:20px;">G.R.I.D OS</h1>
        <p style="color:#6b7280;font-size:11px;letter-spacing:2px;text-transform:uppercase;">Vinculação de Equipamento</p>
        <hr style="border-color:#30363d;margin:24px 0;">
        <p>Um administrador associou o rover <strong style="color:#3ecf8e;">{nome_rover}</strong> à tua conta.</p>
        <p>Quando fizeres registo pela primeira vez, insere o código abaixo para confirmar a vinculação.</p>
        <div style="margin:32px 0;text-align:center;">
            <div style="display:inline-block;background:#12151a;border:2px solid #3ecf8e;border-radius:16px;padding:24px 40px;">
                <p style="color:#6b7280;font-size:10px;letter-spacing:3px;text-transform:uppercase;margin:0 0 12px 0;">Código de Vinculação</p>
                <p style="color:#3ecf8e;font-size:36px;font-weight:800;letter-spacing:12px;margin:0;">{codigo_fmt}</p>
            </div>
        </div>
        <p style="color:#6b7280;font-size:10px;">Guarda este código — será pedido no primeiro acesso.</p>
        <hr style="border-color:#30363d;margin:24px 0;">
        <p style="color:#374151;font-size:9px;letter-spacing:2px;">G.R.I.D OS · PAP 2026</p>
    </div>
    """
    return _enviar_email_mailerlite(destinatario, 'G.R.I.D OS — Rover Vinculado à tua Conta', html)


# ── Painel ────────────────────────────────────────────────────────────────────

def admin_panel():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return redirect(url_for('login'))

    users_list = []
    if supabase:
        try:
            res = supabase.table('users').select('*').execute()
            users_list = res.data if res.data else []
        except Exception:
            pass

    return render_template('admin.html', users=users_list,
                           username=session.get('username'),
                           role=session.get('role'))


# ── Gestão de utilizadores ────────────────────────────────────────────────────

def admin_approve():
    if session.get('role') != 'admin':
        return jsonify({'status': 'unauthorized'}), 403
    username = request.form.get('username')
    try:
        supabase.table('users').update({'aprovado': True, 'bloqueado': False}).eq('username', username).execute()
        return jsonify({'status': 'success'})
    except Exception:
        return jsonify({'status': 'error'}), 500


def admin_reject():
    if session.get('role') != 'admin':
        return jsonify({'status': 'unauthorized'}), 403
    username = request.form.get('username')
    try:
        user = supabase.table('users').select('role').eq('username', username).single().execute()
        if user.data and user.data.get('role') == 'admin':
            return jsonify({'status': 'forbidden', 'message': 'Não é possível remover uma conta admin.'}), 403
        supabase.table('users').delete().eq('username', username).execute()
        return jsonify({'status': 'success'})
    except Exception:
        return jsonify({'status': 'error'}), 500


def admin_revoke():
    if session.get('role') != 'admin':
        return jsonify({'status': 'unauthorized'}), 403
    username = request.form.get('username')
    try:
        user = supabase.table('users').select('role').eq('username', username).single().execute()
        if user.data and user.data.get('role') == 'admin':
            return jsonify({'status': 'forbidden', 'message': 'Não é possível bloquear uma conta admin.'}), 403
        supabase.table('users').update({'aprovado': False, 'bloqueado': True}).eq('username', username).execute()
        return jsonify({'status': 'success'})
    except Exception:
        return jsonify({'status': 'error'}), 500


def admin_change_role():
    if session.get('role') != 'admin':
        return jsonify({'status': 'unauthorized'}), 403
    username = request.form.get('username')
    new_role = request.form.get('role')
    try:
        supabase.table('users').update({'role': new_role}).eq('username', username).execute()
        return jsonify({'status': 'success'})
    except Exception:
        return jsonify({'status': 'error'}), 500


def admin_bind_rover():
    if session.get('role') != 'admin':
        return jsonify({'status': 'unauthorized'}), 403
    username = request.form.get('username')
    rover_id = request.form.get('rover_id')
    try:
        rid = int(rover_id) if rover_id and rover_id != 'Nenhum' else None
        supabase.table('users').update({'rover_id': rid}).eq('username', username).execute()
        if rid:
            supabase.table('rovers').update({'ativo': True}).eq('id', rid).execute()
        return jsonify({'status': 'success'})
    except Exception:
        return jsonify({'status': 'error'}), 500


# ── Gestão de Rovers ──────────────────────────────────────────────────────────

def admin_add_rover():
    if session.get('role') != 'admin':
        return jsonify({'status': 'unauthorized'}), 403

    mac_address = request.form.get('mac_address', '').strip().upper()
    nome        = request.form.get('nome', '').strip()
    email       = request.form.get('email', '').strip().lower()

    if not mac_address or not nome or not email:
        return jsonify({'status': 'error', 'message': 'Preenche todos os campos.'}), 400

    try:
        dup = supabase.table('rovers').select('id').eq('mac_address', mac_address).execute()
        if dup.data:
            return jsonify({'status': 'error', 'message': 'Este MAC address já está registado.'}), 409

        codigo = f'{secrets.randbelow(1000000):06d}'

        supabase.table('rovers').insert({
            'mac_address': mac_address,
            'nome':        nome,
            'codigo':      codigo,
            'ativo':       False,
            'email_dono':  email,
        }).execute()

        enviado = _enviar_email_rover(email, nome, codigo)

        return jsonify({
            'status':        'success',
            'email_enviado': enviado,
            'message':       f'Rover "{nome}" registado. Email {"enviado" if enviado else "não enviado (verificar SMTP)"}.'
        })
    except Exception as e:
        print(f'[ADD ROVER] {e}')
        return jsonify({'status': 'error', 'message': 'Erro ao registar rover.'}), 500


def admin_list_rovers():
    if session.get('role') != 'admin':
        return jsonify({'status': 'unauthorized'}), 403
    try:
        res = supabase.table('rovers').select('*').order('criado_em', desc=True).execute()
        return jsonify({'status': 'success', 'rovers': res.data or []})
    except Exception:
        return jsonify({'status': 'error', 'rovers': []}), 500


def admin_delete_rover():
    if session.get('role') != 'admin':
        return jsonify({'status': 'unauthorized'}), 403
    rover_id = request.form.get('rover_id')
    try:
        rid = int(rover_id)
        supabase.table('users').update({'rover_id': None}).eq('rover_id', rid).execute()
        supabase.table('rovers').delete().eq('id', rid).execute()
        return jsonify({'status': 'success'})
    except Exception:
        return jsonify({'status': 'error'}), 500