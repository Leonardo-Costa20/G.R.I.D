import secrets
from datetime import datetime, timezone
from flask import render_template, request, redirect, url_for, session
from core import supabase, hash_password, check_password, enviar_email_reset


def login():
    error = None
    if request.method == 'POST':
        login_input = request.form.get('login_identity', '').strip()
        pass_input = request.form.get('password')
        if supabase:
            try:
                res = supabase.table('users').select('*').or_(f'username.eq.{login_input},email.eq.{login_input}').execute()
                if res.data:
                    user = res.data[0]
                    stored_pw = user.get('password', '')

                    if stored_pw.startswith('$2b$') or stored_pw.startswith('$2a$'):
                        pw_ok = check_password(pass_input, stored_pw)
                    else:
                        pw_ok = (pass_input == stored_pw)
                        if pw_ok:
                            try:
                                supabase.table('users').update({'password': hash_password(pass_input)}).eq('id', user['id']).execute()
                            except Exception:
                                pass

                    if pw_ok:
                        if not user.get('aprovado', False):
                            if user.get('bloqueado', False):
                                return render_template('login.html', error='ACESSO NEGADO: CONTA BLOQUEADA.')
                            return render_template('login.html', error='ACESSO RETIDO: AGUARDE APROVAÇÃO.')
                        session['logged_in'] = True
                        session['username'] = user['username']
                        session['role'] = str(user.get('role', 'viewer')).strip().lower()
                        return redirect(url_for('index'))
                error = 'ACESSO NEGADO: CREDENCIAIS INVÁLIDAS.'
            except Exception:
                error = 'ERRO NA LIGAÇÃO À BASE DE DADOS.'
    return render_template('login.html', error=error)


def register():
    msg = None
    if request.method == 'POST':
        data = {
            'email': request.form.get('email', '').strip().lower(),
            'username': request.form.get('username', '').strip(),
            'password': hash_password(request.form.get('password', '')),
            'aprovado': False,
            'role': 'viewer',
            'rover_vinculado': 'Nenhum'
        }
        if supabase:
            try:
                supabase.table('users').insert(data).execute()
                msg = 'CONTA CRIADA! AGUARDE APROVAÇÃO.'
            except Exception:
                msg = 'ERRO AO INSERIR UTILIZADOR.'
    return render_template('register.html', msg=msg)


def logout():
    session.clear()
    return redirect(url_for('welcome'))


def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        try:
            user = supabase.table('users').select('email').eq('email', email).maybe_single().execute()
            if user.data:
                codigo = f"{secrets.randbelow(1000000):06d}"
                created_at = datetime.now(timezone.utc).isoformat()
                supabase.table('password_resets').delete().eq('email', email).execute()
                supabase.table('password_resets').insert({
                    'email': email,
                    'token': codigo,
                    'created_at': created_at
                }).execute()
                print(f'[RESET] Código gerado para {email}: {codigo}')
                enviar_email_reset(email, codigo)
        except Exception as e:
            print(f'[FORGOT ERROR] {e}')
        return render_template('forgot_password.html', step='verify', email=email, msg='Se o email existir, receberás o código em breve.', msg_type='success')
    return render_template('forgot_password.html', step='email')


def verify_code():
    email = request.form.get('email', '').strip().lower()
    codigo = request.form.get('codigo', '').replace(' ', '').strip()
    error = None
    try:
        res = supabase.table('password_resets').select('*').eq('email', email).maybe_single().execute()
        if res.data:
            created = datetime.fromisoformat(res.data['created_at'].replace('Z', '+00:00'))
            agora = datetime.now(timezone.utc)
            delta = (agora - created).total_seconds()
            if delta > 900:
                error = 'CÓDIGO EXPIRADO. SOLICITA UM NOVO.'
            elif str(res.data['token']).strip() != codigo:
                error = 'CÓDIGO INVÁLIDO. TENTA NOVAMENTE.'
            else:
                session['reset_email'] = email
                session['reset_verified'] = True
                return redirect(url_for('reset_password'))
        else:
            error = 'NENHUM PEDIDO ENCONTRADO PARA ESTE EMAIL.'
    except Exception as e:
        print(f'[VERIFY ERROR] {e}')
        error = 'ERRO AO VERIFICAR O CÓDIGO.'
    return render_template('forgot_password.html', step='verify', email=email, error=error)


def reset_password():
    if not session.get('reset_verified') or not session.get('reset_email'):
        return redirect(url_for('forgot_password'))
    email = session['reset_email']
    error = None
    if request.method == 'POST':
        nova_pw = request.form.get('password', '')
        confirmar = request.form.get('confirm_password', '')
        if len(nova_pw) < 6:
            error = 'A PASSWORD DEVE TER PELO MENOS 6 CARACTERES.'
        elif nova_pw != confirmar:
            error = 'AS PASSWORDS NÃO COINCIDEM.'
        else:
            try:
                supabase.table('users').update({'password': hash_password(nova_pw)}).eq('email', email).execute()
                supabase.table('password_resets').delete().eq('email', email).execute()
                session.pop('reset_email', None)
                session.pop('reset_verified', None)
                return render_template('login.html', success='PASSWORD ATUALIZADA! FAZ LOGIN.')
            except Exception:
                error = 'ERRO AO ATUALIZAR A BASE DE DADOS.'
    return render_template('reset_password.html', error=error)