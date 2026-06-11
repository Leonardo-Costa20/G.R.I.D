import email
import re
import secrets
from datetime import datetime, timezone
from flask import render_template, request, redirect, url_for, session
from core import supabase, hash_password, check_password, enviar_email_reset


# ── Helpers de validação ──────────────────────────────────────────────────────

def is_valid_email(email: str) -> bool:
    """Valida formato de email básico (exige @, domínio e extensão)."""
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def is_valid_username(username: str) -> bool:
    """3–20 chars, só letras, números, _ e -."""
    return bool(re.match(r'^[a-zA-Z0-9_\-]{3,20}$', username))

def validate_password(password: str):
    """Devolve lista de erros ou lista vazia se OK."""
    errors = []
    if len(password) < 8:
        errors.append('A password deve ter pelo menos 8 caracteres.')
    if not re.search(r'[A-Z]', password):
        errors.append('A password deve conter pelo menos uma letra maiúscula.')
    if not re.search(r'[0-9]', password):
        errors.append('A password deve conter pelo menos um número.')
    return errors


# ── Rotas ─────────────────────────────────────────────────────────────────────

def login():
    error = None
    if request.method == 'POST':
        login_input = request.form.get('login_identity', '').strip()
        pass_input  = request.form.get('password', '')

        if not login_input or not pass_input:
            error = 'PREENCHE TODOS OS CAMPOS.'
            return render_template('login.html', error=error)

        if supabase:
            try:
                res = supabase.table('users').select('*').or_(
                    f'username.eq.{login_input},email.eq.{login_input}'
                ).execute()

                if res.data:
                    user      = res.data[0]
                    stored_pw = user.get('password', '')

                    if stored_pw.startswith('$2b$') or stored_pw.startswith('$2a$'):
                        pw_ok = check_password(pass_input, stored_pw)
                    else:
                        pw_ok = (pass_input == stored_pw)
                        if pw_ok:
                            try:
                                supabase.table('users').update(
                                    {'password': hash_password(pass_input)}
                                ).eq('id', user['id']).execute()
                            except Exception:
                                pass

                    if pw_ok:
                        if not user.get('aprovado', False):
                            if user.get('bloqueado', False):
                                return render_template('login.html', error='ACESSO NEGADO: CONTA BLOQUEADA.')
                            return render_template('login.html', error='ACESSO RETIDO: AGUARDE APROVAÇÃO.')
                        session['logged_in'] = True
                        session['username']  = user['username']
                        session['role']      = str(user.get('role', 'viewer')).strip().lower()
                        return redirect(url_for('index'))

                error = 'ACESSO NEGADO: CREDENCIAIS INVÁLIDAS.'
            except Exception:
                error = 'ERRO NA LIGAÇÃO À BASE DE DADOS.'

    return render_template('login.html', error=error)


def register():
    msg      = None
    msg_type = 'success'
    errors   = []

    if request.method == 'POST':
        email     = request.form.get('email', '').strip().lower()
        username  = request.form.get('username', '').strip()
        password  = request.form.get('password', '')
        confirm   = request.form.get('confirm_password', '')
        telemovel = request.form.get('telemovel', '').strip().replace(' ', '')

        # ── Validações front-end duplicadas no servidor ───────────────────────
        if not email:
            errors.append('O email é obrigatório.')
        elif not is_valid_email(email):
            errors.append('Insere um endereço de email válido (ex: nome@dominio.pt).')

        if not username:
            errors.append('O nome de utilizador é obrigatório.')
        elif not is_valid_username(username):
            errors.append('O username deve ter 3–20 caracteres e só pode conter letras, números, _ ou -.')

        if not telemovel:
            errors.append('O número de telemóvel é obrigatório.')
        elif not re.match(r'^(\+351)?9[1236]\d{7}$|^\+?\d{7,15}$', telemovel):
            errors.append('Número de telemóvel inválido. Ex: 912345678 ou +351912345678')

        pw_errors = validate_password(password)
        errors.extend(pw_errors)

        if password != confirm:
            errors.append('As passwords não coincidem.')

        if errors:
            return render_template('register.html', errors=errors, form=request.form)

        # ── Verificar duplicados ──────────────────────────────────────────────
        if supabase:
            try:
                dup_email = supabase.table('users').select('id').eq('email', email).execute()
                if dup_email.data:
                    return render_template('register.html',
                                           errors=['Este email já está registado.'],
                                           form=request.form)

                dup_user = supabase.table('users').select('id').eq('username', username).execute()
                if dup_user.data:
                    return render_template('register.html',
                                           errors=['Este nome de utilizador já está em uso.'],
                                           form=request.form)

                # Verificar se existe um rover pendente para este email antes de inserir
                rover_pendente = None
                rover_id_pendente = None
                try:
                    rv = supabase.table('rovers').select('id, nome') \
                        .eq('email_dono', email).eq('ativo', False).maybe_single().execute()
                    if rv.data:
                        rover_pendente    = rv.data
                        rover_id_pendente = rv.data['id']
                except Exception:
                    pass

                data = {
                    'email':     email,
                    'username':  username,
                    'password':  hash_password(password),
                    'telemovel': telemovel,
                    'aprovado':  False,
                    'role':      'viewer',
                }
                if rover_id_pendente:
                    data['rover_id'] = rover_id_pendente

                supabase.table('users').insert(data).execute()

                msg      = 'CONTA CRIADA! AGUARDA APROVAÇÃO DO ADMINISTRADOR.'
                msg_type = 'success'
                return render_template('register.html',
                                       msg=msg,
                                       msg_type=msg_type,
                                       rover_vinculado=rover_pendente,
                                       rover_email=email if rover_pendente else None)

            except Exception as e:
                print(f'[REGISTER ERROR] {e}')
                msg      = 'ERRO AO CRIAR CONTA. TENTA NOVAMENTE.'
                msg_type = 'error'

    return render_template('register.html', msg=msg, msg_type=msg_type)


def logout():
    session.clear()
    return redirect(url_for('welcome'))


def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()

        if not is_valid_email(email):
            return render_template('forgot_password.html',
                                   step='email',
                                   error='Insere um endereço de email válido.')

        try:
            user = supabase.table('users').select('email').eq('email', email).maybe_single().execute()
            if user.data:
                codigo     = f'{secrets.randbelow(1000000):06d}'
                created_at = datetime.now(timezone.utc).isoformat()

                supabase.table('password_resets').upsert({
                'email':      email,
                'token':      codigo,
                'created_at': created_at,
                }).execute()
                print(f'[RESET] Código gerado para {email}: {codigo}')
                enviar_email_reset(email, codigo)
        except Exception as e:
            print(f'[FORGOT ERROR] {e}')

        return render_template('forgot_password.html',
                               step='verify',
                               email=email,
                               msg='Se o email existir, receberás o código em breve.',
                               msg_type='success')

    return render_template('forgot_password.html', step='email')


def verify_code():
    email  = request.form.get('email', '').strip().lower()
    codigo = request.form.get('codigo', '').replace(' ', '').strip()
    error  = None

    try:
        res = supabase.table('password_resets').select('*').eq('email', email).maybe_single().execute()
        if res.data:
            created = datetime.fromisoformat(res.data['created_at'].replace('Z', '+00:00'))
            agora   = datetime.now(timezone.utc)
            delta   = (agora - created).total_seconds()

            if delta > 900:
                error = 'CÓDIGO EXPIRADO. SOLICITA UM NOVO.'
            elif str(res.data['token']).strip() != codigo:
                error = 'CÓDIGO INVÁLIDO. TENTA NOVAMENTE.'
            else:
                session['reset_email']    = email
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
        nova_pw   = request.form.get('password', '')
        confirmar = request.form.get('confirm_password', '')

        pw_errors = validate_password(nova_pw)
        if pw_errors:
            error = pw_errors[0]
        elif nova_pw != confirmar:
            error = 'AS PASSWORDS NÃO COINCIDEM.'
        else:
            try:
                supabase.table('users').update(
                    {'password': hash_password(nova_pw)}
                ).eq('email', email).execute()
                supabase.table('password_resets').delete().eq('email', email).execute()
                session.pop('reset_email', None)
                session.pop('reset_verified', None)
                return render_template('login.html', success='PASSWORD ATUALIZADA! FAZ LOGIN.')
            except Exception:
                error = 'ERRO AO ATUALIZAR A BASE DE DADOS.'

    return render_template('reset_password.html', error=error)