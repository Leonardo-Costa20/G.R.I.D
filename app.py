import os
import threading
from flask import Flask
from core import SECRET_KEY, socketio, inicializar_contador_logs, monitor_infraestrutura_loop, initialize_mqtt
from routes import register_routes

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = SECRET_KEY
socketio.init_app(app)
register_routes(app)

if __name__ == '__main__':
    inicializar_contador_logs()
    initialize_mqtt()
    t = threading.Thread(target=monitor_infraestrutura_loop, daemon=True)
    t.start()
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
