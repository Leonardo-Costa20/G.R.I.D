"""
SCRIPT DE MIGRAÇÃO — Corre UMA VEZ no servidor.
Converte todas as passwords em texto plano para bcrypt.
"""
import os
import bcrypt
from dotenv import load_dotenv
from supabase import create_client
 
load_dotenv()
 
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
 
def migrar():
    res = supabase.table("users").select("id, username, password").execute()
    users = res.data or []
    
    migrados = 0
    ja_cifrados = 0
    
    for user in users:
        pw = user.get('password', '')
        
        # Já está em bcrypt — salta
        if pw.startswith('$2b$') or pw.startswith('$2a$'):
            ja_cifrados += 1
            print(f"  ⏭️  {user['username']} — já cifrado")
            continue
        
        # Está em texto plano — cifra e atualiza
        hashed = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
        supabase.table("users").update({"password": hashed}).eq("id", user['id']).execute()
        migrados += 1
        print(f"  ✅ {user['username']} — migrado")
    
    print(f"\nFeito: {migrados} migrados, {ja_cifrados} já estavam cifrados.")
 
if __name__ == '__main__':
    print("A migrar passwords...\n")
    migrar()