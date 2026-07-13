from gevent import monkey
monkey.patch_all()

import os
import threading
import mimetypes
mimetypes.add_type('application/manifest+json', '.json')

from flask import Flask
from core import SECRET_KEY, socketio, inicializar_contador_logs, monitor_infraestrutura_loop, initialize_mqtt
from routes import register_routes

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = SECRET_KEY
socketio.init_app(app)
register_routes(app)

# Arranca MQTT e threads sempre — tanto em dev como em produção com Gunicorn
inicializar_contador_logs()
initialize_mqtt()
t = threading.Thread(target=monitor_infraestrutura_loop, daemon=True)
t.start()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
