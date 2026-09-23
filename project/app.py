import os
from flask import Flask
from dotenv import load_dotenv

from extensions import db, socketio, migrate
from users import users_bp
from rooms import rooms_bp
import sockets  # noqa: F401 (소켓 이벤트 등록용 import)

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URI")

db.init_app(app)
migrate.init_app(app, db)
socketio.init_app(app, logger=True)  # 개발 중 소켓 핸들러 예외를 콘솔에서 볼 수 있도록 켜둠

app.register_blueprint(users_bp)
app.register_blueprint(rooms_bp)


if __name__ == "__main__":
    socketio.run(app, debug=True, port=8080)
