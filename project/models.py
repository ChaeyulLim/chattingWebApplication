from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class UserInfo(db.Model):
    __tablename__ = "USER_INFO"

    UI_ID = db.Column(db.String(50), primary_key=True)
    UI_PW = db.Column(db.String(255), nullable=False)
    UI_NAME = db.Column(db.String(50), nullable=False)
    UI_MAIL = db.Column(db.String(50), nullable=False, unique=True)
    UI_RDATE = db.Column(db.Date, nullable=False)
    UI_WITHDRAWN = db.Column(db.Date, nullable=True)

class RoomInfo(db.Model):
    __tablename__ = "ROOM_INFO"

    RI_ID = db.Column(db.Integer, primary_key=True)
    RI_NAME = db.Column(db.String(50), nullable=True)
    RI_TYPE = db.Column(db.CHAR(1), nullable=False)
    RI_RDATE = db.Column(db.Date, nullable=False)

class RoomMember(db.Model):
    __tablename__ = "ROOM_MEMBER"

    RM_ID = db.Column(db.Integer, primary_key=True)
    RI_ID = db.Column(db.Integer, db.ForeignKey("ROOM_INFO.RI_ID"), nullable=False)
    UI_ID = db.Column(db.String(50), db.ForeignKey("USER_INFO.UI_ID"), nullable=False)

class ChatMessage(db.Model):
    __tablename__ = "CHAT_MESSAGE"

    CM_ID = db.Column(db.Integer, primary_key=True)
    RI_ID = db.Column(db.Integer, db.ForeignKey("ROOM_INFO.RI_ID"), nullable=False)
    UI_ID = db.Column(db.String(50), db.ForeignKey("USER_INFO.UI_ID"), nullable=False)
    CM_MESSAGE = db.Column(db.String(255), nullable=False)
    CM_DATE = db.Column(db.DateTime, nullable=False)

