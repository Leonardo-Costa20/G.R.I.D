# G.R.I.D OS

**Ground Recon & Intelligent Detection** — Aplicação web que recebe, processa e apresenta os dados do rover G.R.I.D em tempo real.

**Acesso:** [gridos.space](https://gridos.space)

---

## Visão Geral

O G.R.I.D OS é o "cérebro" do sistema G.R.I.D — uma aplicação web que recebe os dados enviados pelo rover, processa-os e apresenta-os numa interface de controlo. A comunicação com o rover é feita via **MQTT over TLS**, os dados são persistidos no **Supabase** e a interface atualiza em tempo real via **WebSockets (Socket.IO)**. O vídeo do rover é transmitido diretamente pelo **ESP32-CAM** e exposto publicamente através de um **Cloudflare Tunnel**.

---

## Funcionalidades

- **Dashboard em tempo real** — visualização de dados de sensores, estado do rover e métricas do sistema
- **Câmara em direto** — stream de vídeo do ESP32-CAM montado no rover, exposto através de túnel seguro (Cloudflare Tunnel)
- **Controlo do rover** — joystick virtual com comandos de direção e velocidade
- **Autenticação** — registo, login, recuperação de password por email e sistema de aprovação por administrador
- **Vinculação de rover** — associação de rovers a utilizadores via código enviado por email
- **Painel de administração** — gestão de utilizadores (aprovar, bloquear, alterar cargo) e gestão de rovers
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
| Email | Gmail API + OAuth2 |
| Frontend | HTML/CSS/JS + Tailwind CSS + Socket.IO client |
| Deploy | Gunicorn + Gevent |
| Stream de vídeo | ESP32-CAM + Cloudflare Tunnel |

---

## Estrutura do Projeto

```
G.R.I.D/
├── app.py                          # Ponto de entrada da aplicação
├── core.py                         # Configurações globais, MQTT, Socket.IO, helpers
├── bridge.py                       # Bridge MQTT → Supabase (script independente)
├── requirements.txt                # Dependências Python
├── Procfile                        # Configuração de deploy (Gunicorn)
├── grid.sql                        # Schema da base de dados (Supabase/PostgreSQL)
├── .env                            # Variáveis de ambiente (não commitar)
├── routes/
│   ├── __init__.py                 # Registo de todas as rotas
│   ├── auth.py                     # Login, registo, recuperação de password
│   ├── main.py                     # Landing page, welcome, dashboard
│   ├── rover.py                    # Comandos WebSocket + vinculação de rover
│   ├── logs.py                     # Página de logs + API de exportação
│   ├── admin.py                    # Painel de administração
│   └── profile.py                  # Definições de perfil e rover do utilizador
├── templates/                      # Templates HTML (Jinja2)
│   ├── index.html                  # Dashboard principal
│   ├── _sidebar.html               # Sidebar partilhada
│   ├── login.html                  # Página de login
│   ├── register.html               # Página de registo
│   ├── forgot_password.html        # Recuperação de password
│   ├── reset_password.html         # Redefinição de password
│   ├── landing_apresentacao.html   # Landing page
│   ├── welcome.html                # Boas-vindas pós-registo
│   ├── settings.html               # Definições do utilizador
│   ├── logs.html                   # Histórico de logs
│   └── admin.html                  # Painel de administração
├── static/                         # CSS, JS, ícones, manifest PWA
│   ├── css/
│   │   ├── style.css               # Estilos globais
│   │   └── joystick.css            # Estilos do joystick
│   ├── js/
│   │   ├── i18n.js                 # Internacionalização
│   │   └── joystick.js             # Lógica do joystick
│   ├── icons/                      # Ícones PWA
│   ├── logo.png                    # Logótipo
│   ├── manifest.json               # Manifest PWA
│   └── sw.js                       # Service Worker
├── cod_esp32_final/
│   └── cod_esp32_final.ino         # Firmware do ESP32 (rover: sensores + MQTT)
└── cod_esp32cam_final/
    ├── cod_esp32cam_final.ino      # Firmware do ESP32-CAM (stream de vídeo)
    ├── app_httpd.cpp               # Servidor HTTP da câmara
    ├── board_config.h              # Pinout do módulo de câmara
    ├── camera_pins.h               # Mapeamento de pinos GPIO
    ├── camera_index.h              # Interface web embutida
    └── partitions.csv              # Esquema de partições flash
```

---

## Instalação e Execução

### Pré-requisitos

- Python 3.12+
- Conta no [Supabase](https://supabase.com)
- Broker MQTT (configurado por omissão para HiveMQ Cloud)
- Conta Gmail com OAuth2 ativo (Client ID, Client Secret e Refresh Token)

### 1. Clonar o repositório

```bash
git clone https://github.com/Leonardo-Costa20/G.R.I.D.git
cd G.R.I.D
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar a base de dados

No painel do Supabase, abre o **SQL Editor** e executa o ficheiro `grid.sql`. Isto cria as tabelas `users`, `rovers`, `logs_operacao` e `password_resets`.

### 4. Configurar as variáveis de ambiente

Cria um ficheiro `.env` na raiz do projeto:

```env
FLASK_SECRET_KEY=<chave-secreta-aleatória>
SUPABASE_URL=<url-do-teu-projeto-supabase>
SUPABASE_KEY=<anon-key-do-supabase>
MQTT_BROKER=<broker.hivemq.cloud>
MQTT_PORT=8883
MQTT_USERNAME=<utilizador-mqtt>
MQTT_PASSWORD=<password-mqtt>
GMAIL_CLIENT_ID=<client-id-do-oauth2>
GMAIL_CLIENT_SECRET=<client-secret-do-oauth2>
GMAIL_REFRESH_TOKEN=<refresh-token-do-oauth2>
GMAIL_SENDER=<o-teu-email@gmail.com>
```

>  **Nunca commites o ficheiro `.env` com credenciais reais.**

Para obter as credenciais Gmail OAuth2, consulta a secção [Configuração do Gmail OAuth2](#configuração-do-gmail-oauth2) abaixo.

### 5. Iniciar o servidor

```bash
python app.py
```

O servidor fica disponível em `http://localhost:5000`.

### Bridge (opcional)

Para correr a bridge MQTT → Supabase de forma independente (sem o servidor web):

```bash
python bridge.py
```

---

## Para o sistema funcionar na totalidade

Precisas de ter estes quatro componentes a correr em simultâneo:

| # | Componente | Como arrancar |
|---|---|---|
| 1 | **Servidor web** | `python app.py` no PC/servidor |
| 2 | **ESP32 (rover)** | Firmware carregado e rover ligado à corrente |
| 3 | **ESP32-CAM** | Firmware carregado e módulo ligado à corrente |
| 4 | **Cloudflare Tunnel** | `cloudflared tunnel run grid-cam` no PC da rede local |

---

## Configuração do ESP32 (rover)

Abre `cod_esp32_final/cod_esp32_final.ino` no Arduino IDE e edita as credenciais no topo do ficheiro:

```cpp
const char* ssid     = "O_TEU_WIFI";
const char* password = "A_TUA_PASSWORD";
```

**Bibliotecas Arduino necessárias** (instala via Library Manager):
- `PubSubClient`
- `Adafruit ADXL345`
- `Adafruit BMP280`
- `Adafruit Unified Sensor`

Carrega o sketch para o ESP32 e o rover fica a publicar dados via MQTT.

---

## Configuração da Câmara (ESP32-CAM + Cloudflare Tunnel)

O stream de vídeo é fornecido pelo **ESP32-CAM** e exposto publicamente através de um **Cloudflare Tunnel** a correr num PC na mesma rede local do rover. Sem o túnel ativo, a câmara não fica acessível a partir da aplicação web.

### 1. Flash do firmware

Abre `cod_esp32cam_final/cod_esp32cam_final.ino` no Arduino IDE e edita as credenciais Wi-Fi:

```cpp
const char *ssid     = "O_TEU_WIFI";
const char *password = "A_TUA_PASSWORD";
```

Carrega o sketch para o ESP32-CAM. Após o boot, o endereço IP local aparece no Monitor Série (ex.: `192.168.1.42`). O stream está disponível em `http://<IP>/stream`.

### 2. Instalar o cloudflared

```bash
# Linux / macOS
brew install cloudflare/cloudflare/cloudflared

# Windows — descarrega o binário em:
https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
```

### 3. Criar o tunnel (apenas na primeira vez)

```bash
cloudflared tunnel login
cloudflared tunnel create grid-cam
```

Guarda o UUID apresentado após o segundo comando.

### 4. Configurar o `config.yml`

Cria o ficheiro em `~/.cloudflared/config.yml` (Linux/macOS) ou `%USERPROFILE%\.cloudflared\config.yml` (Windows):

```yaml
tunnel: <UUID-DO-TEU-TUNNEL>
credentials-file: /home/<user>/.cloudflared/<UUID-DO-TEU-TUNNEL>.json

ingress:
  - hostname: cam.gridos.space
    service: http://192.168.1.42    # IP local do ESP32-CAM
  - service: http_status:404
```

> **Nota:** O IP do ESP32-CAM pode mudar a cada arranque. Para o fixar, reserva o IP no router (DHCP reservation) ou configura um IP estático no firmware.

### 5. Iniciar o tunnel

```bash
cloudflared tunnel run grid-cam
```

Mantém este processo a correr enquanto o rover estiver em operação.

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
| `rover_status_update` | Estado do rover `{ status: 'online'\|'offline' }` |
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

