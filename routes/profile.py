from flask import render_template, request, jsonify, session, redirect, url_for
from core import supabase, hash_password, check_password


def settings_page():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    email = ''
    if supabase:
        try:
            res = supabase.table('users').select('email').eq('username', session['username']).single().execute()
            email = res.data.get('email', '') if res.data else ''
        except Exception:
            pass

    return render_template('settings.html', username=session.get('username'), role=session.get('role'), email=email)


def api_profile():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    if not supabase:
        return jsonify({'error': 'Database unavailable'}), 503

    data = request.get_json(silent=True) or {}
    new_username = data.get('username', '').strip()
    new_email = data.get('email', '').strip().lower()

    if not new_username:
        return jsonify({'error': 'Username não pode estar vazio.'}), 400

    try:
        update = {'username': new_username}
        if new_email:
            update['email'] = new_email
        supabase.table('users').update(update).eq('username', session['username']).execute()
        session['username'] = new_username
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def api_change_password():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    if not supabase:
        return jsonify({'error': 'Database unavailable'}), 503

    data = request.get_json(silent=True) or {}
    current = data.get('current', '')
    new_password = data.get('new_password', '')

    if len(new_password) < 6:
        return jsonify({'error': 'A nova password deve ter pelo menos 6 caracteres.'}), 400

    try:
        res = supabase.table('users').select('password').eq('username', session['username']).single().execute()
        if not res.data:
            return jsonify({'error': 'Utilizador não encontrado.'}), 404
        if not check_password(current, res.data['password']):
            return jsonify({'error': 'Password atual incorreta.'}), 403
        supabase.table('users').update({'password': hash_password(new_password)}).eq('username', session['username']).execute()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def api_rover_status():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    if not supabase:
        return jsonify({'rover': 'Nenhum'})
    try:
        res = supabase.table('users').select('rover_vinculado').eq('username', session['username']).single().execute()
        return jsonify({'rover': res.data.get('rover_vinculado', 'Nenhum') if res.data else 'Nenhum'})
    except Exception:
        return jsonify({'rover': 'Nenhum'})


def api_rover_link():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    if not supabase:
        return jsonify({'error': 'Database unavailable'}), 503

    data = request.get_json(silent=True) or {}
    rover_id = data.get('rover_id', '').strip()
    if not rover_id:
        return jsonify({'error': 'rover_id é obrigatório.'}), 400

    try:
        supabase.table('users').update({'rover_vinculado': rover_id}).eq('username', session['username']).execute()
        return jsonify({'status': 'ok', 'rover_vinculado': rover_id})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def api_rover_unlink():
    if not session.get('logged_in'):
        return jsonify({'error': 'Unauthorized'}), 401
    if not supabase:
        return jsonify({'error': 'Database unavailable'}), 503

    try:
        supabase.table('users').update({'rover_vinculado': 'Nenhum'}).eq('username', session['username']).execute()
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
