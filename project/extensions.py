from flask_socketio import SocketIO
from flask_migrate import Migrate

from models import db

socketio = SocketIO()
migrate = Migrate()
