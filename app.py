import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session
from supabase import create_client, Client

# 1. CARREGAR CONFIGURAÇÕES (.env)
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# 2. CONFIGURAÇÃO SUPABASE
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
supabase: Client = create_client(url, key)

# --- ROTAS ---

@app.route('/')
def landing():
    """Página de entrada (Landing Page) - Onde está o botão 'COMEÇAR'."""
    # Se já estiver logado, podemos mandar direto para o dashboard, 
    # mas para a apresentação da PAP, normalmente mostras a landing primeiro.
    return render_template('landing.html')

@app.route('/dashboard')
def index():
    """Dashboard principal - Protegido por Login."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html', username=session.get('username'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        login_input = request.form.get('login_identity').strip()
        pass_input = request.form.get('password')
        
        try:
            # Procura na tabela se o input coincide com username OU email
            res = supabase.table("users").select("*")\
                .or_(f"username.eq.{login_input},email.eq.{login_input}")\
                .eq("password", pass_input)\
                .execute()
            
            if res.data:
                session['logged_in'] = True
                session['username'] = res.data[0]['username']
                # Após login com sucesso, vai para o dashboard
                return redirect(url_for('index'))
            else:
                error = "ACESSO NEGADO: CREDENCIAIS INVÁLIDAS."
        except Exception as e:
            print(f"DEBUG LOGIN: {e}")
            error = "ERRO TÉCNICO NA AUTENTICAÇÃO."
            
    return render_template('login.html', error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = None
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        username = request.form.get('username').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if password != confirm_password:
            msg = "ERRO: AS PASSWORDS NÃO COINCIDEM."
        else:
            try:
                # Prepara os dados para o Supabase conforme a tua tabela
                data = {
                    "email": email,
                    "username": username, 
                    "password": password, 
                    "aprovado": True
                }
                
                supabase.table("users").insert(data).execute()
                msg = "CONTA CRIADA! PODES FAZER LOGIN."
                
            except Exception as e:
                print("\n" + "="*30)
                print("DEBUG REGISTRO (ERRO REAL):")
                print(e)
                print("="*30 + "\n")
                
                if "duplicate" in str(e).lower():
                    msg = "ERRO: ESTE UTILIZADOR OU EMAIL JÁ EXISTE."
                else:
                    msg = "ERRO NA TABELA: VERIFICA O TERMINAL DO VS CODE."
                
    return render_template('register.html', msg=msg)

@app.route('/logout')
def logout():
    """Faz logout e volta para a Landing Page inicial."""
    session.clear()
    return redirect(url_for('landing'))

if __name__ == '__main__':
    # Garante que o Flask corre na porta 5000
    app.run(debug=True, port=5000)