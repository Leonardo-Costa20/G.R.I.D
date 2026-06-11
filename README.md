# G.R.I.D OS

**Ground Recon & Intelligent Detection** — Sistema operativo web que recebe, processa e apresenta os dados do rover G.R.I.D em tempo real.

---

## Visão Geral

O G.R.I.D OS é o "cérebro" do sistema G.R.I.D — uma aplicação web que recebe os dados enviados pelo rover, processa-os e apresenta-os numa interface de controlo. A comunicação com o rover é feita via **MQTT over TLS**, os dados são persistidos no **Supabase** e a interface atualiza em tempo real via **WebSockets (Socket.IO)**.

---

## Funcionalidades

- **Dashboard em tempo real** — visualização de dados de sensores, estado do rover e métricas do sistema
- **Controlo do rover** — joystick virtual com comandos de direção e velocidade
- **Autenticação** — registo, login, recuperação de password por email e sistema de aprovação por administrador
- **Vinculação de rover** — associação de rovers a utilizadores via código enviado por email
- **Painel de administração** — gestão de utilizadores (aprovar, bloquear, alterar papel) e gestão de rovers
- **Logs de operação** — histórico filtrável de eventos e leituras de sensores, com exportação em CSV e PDF
- **PWA** — instalável como app nativa (manifest + service worker incluídos)
- **Bridge autónoma** — script independente para persistir dados MQTT no Supabase sem o servidor web

---

## Stack Tecnológico

| Camada | Tecnologia |
|---|---|
| Backend | Python 3.12 + Flask + Flask-SocketIO |
| Base de dados | Supabase (PostgreSQL) |
| Comunicação IoT | MQTT (HiveMQ Cloud, TLS porta 8883) |
| Email | MailerLite API |
| Frontend | HTML/CSS/JS + Socket.IO client |
| Deploy | Gunicorn + Eventlet |

---

## Estrutura do Projeto

```
G.R.I.D-main/
├── app.py                  # Ponto de entrada da aplicação
├── core.py                 # Configurações globais, MQTT, Socket.IO, helpers
├── bridge.py               # Bridge MQTT → Supabase (script independente)
├── requirements.txt        # Dependências Python
├── .env                    # Variáveis de ambiente (não commitar)
├── routes/
│   ├── __init__.py         # Registo de todas as rotas
│   ├── auth.py             # Login, registo, recuperação de password
│   ├── main.py             # Landing page, welcome, dashboard
│   ├── rover.py            # Comandos WebSocket + vinculação de rover
│   ├── logs.py             # Página de logs + API de exportação
│   ├── admin.py            # Painel de administração
│   └── profile.py          # Definições de perfil e rover do utilizador
├── templates/              # Templates HTML (Jinja2)
└── static/                 # CSS, JS, ícones, manifest PWA
```

---

## Instalação e Execução

### Pré-requisitos

- Python 3.12+
- Conta no [Supabase](https://supabase.com)
- Broker MQTT (configurado por omissão para HiveMQ Cloud)
- Conta no [MailerLite](https://www.mailerlite.com) (para envio de emails)

### Passos

```bash
# 1. Clonar o repositório
git clone https://github.com/<teu-user>/G.R.I.D.git
cd G.R.I.D-main

# 2. Criar e ativar ambiente virtual
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com as tuas credenciais

# 5. Iniciar o servidor
python app.py
```

O servidor fica disponível em `http://localhost:5000`.

### Bridge (opcional)

Para correr a bridge MQTT → Supabase de forma independente (sem o servidor web):

```bash
python bridge.py
```

---

## Variáveis de Ambiente

Cria um ficheiro `.env` na raiz do projeto com os seguintes valores:

```env
FLASK_SECRET_KEY=<chave-secreta-aleatória>
SUPABASE_URL=<url-do-teu-projeto-supabase>
SUPABASE_KEY=<anon-key-do-supabase>
MAILERLITE_API_KEY=<api-key-do-mailerlite>
```

> ⚠️ **Nunca commites o ficheiro `.env` com credenciais reais.**

---

## API WebSocket

| Evento (cliente → servidor) | Descrição |
|---|---|
| `drive_command` | Envia comando de movimento `{ command, speed }` ao rover via MQTT |
| `connect` | Regista cliente; recebe estado atual do rover |
| `disconnect` | Remove cliente da contagem |

| Evento (servidor → cliente) | Descrição |
|---|---|
| `mqtt_data` | Leitura de sensor `{ sensor, valor }` |
| `rover_status_update` | Estado do rover `{ status: 'online'|'offline' }` |
| `server_metrics` | Métricas do sistema (latência DB, clientes WS, total de logs, etc.) |

### Comandos de condução disponíveis

`forward` · `backward` · `left` · `right` · `stop` · `forward-left` · `forward-right` · `backward-left` · `backward-right`

---

## Tópicos MQTT

| Tópico | Direção | Descrição |
|---|---|---|
| `G.R.I.D/#` | Rover → Servidor | Leituras de sensores e estado |
| `G.R.I.D/status` | Rover → Servidor | `online` / `offline` |
| `G.R.I.D/drive/command` | Servidor → Rover | Comandos de movimento (JSON) |

---

## Contribuição

1. Faz fork do repositório
2. Cria um branch para a tua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit das alterações (`git commit -m 'feat: descrição'`)
4. Push para o branch (`git push origin feature/nova-funcionalidade`)
5. Abre um Pull Request

---

## Licença

Projeto académico — PAP 2026. Todos os direitos reservados.