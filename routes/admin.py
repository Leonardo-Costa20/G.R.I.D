from flask import render_template, request, jsonify, redirect, url_for, session
from core import supabase


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

    return render_template('admin.html', users=users_list, username=session.get('username'), role=session.get('role'))


def admin_approve():
    if session.get('role') != 'admin':
        return jsonify({'status': 'unauthorized'}), 403
    username = request.form.get('username')
    try:
        supabase.table('users').update({'aprovado': True}).eq('username', username).execute()
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
        supabase.table('users').update({'aprovado': False}).eq('username', username).execute()
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
        supabase.table('users').update({'rover_vinculado': rover_id}).eq('username', username).execute()
        return jsonify({'status': 'success'})
    except Exception:
        return jsonify({'status': 'error'}), 500