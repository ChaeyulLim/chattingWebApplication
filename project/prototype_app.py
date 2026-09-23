from flask import Flask, render_template, request, session, redirect
from flask_socketio import SocketIO, emit, join_room

import os
from dotenv import load_dotenv
from flask_migrate import Migrate
from models import db, UserInfo, RoomInfo, RoomMember, ChatMessage

from datetime import date, datetime
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()


app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")

db.init_app(app)
Migrate(app, db)

socketio = SocketIO(app)

@app.route('/')
def index():
    user_id = session.get("user_id")
    return render_template("index.html", user_id=user_id)

@app.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        
        if not request.form["UserID"].strip():
            print("아이디를 입력해주세요.")
        elif UserInfo.query.filter_by(UI_ID=request.form["UserID"]).first():
            print("이미 가입된 아이디 입니다.")
        elif UserInfo.query.filter_by(UI_MAIL=request.form["UserMail"]).first():
            print("이미 가입된 메일 입니다.")
        else:
            user = UserInfo(
                UI_ID = request.form["UserID"], 
                UI_PW = generate_password_hash(request.form["UserPW"]), 
                UI_NAME = request.form["UserName"], 
                UI_MAIL = request.form["UserMail"], 
                UI_RDATE = date.today(), 
            )
            db.session.add(user)
            db.session.commit()
            print("등록 성공!")
            return redirect("/login")

    return render_template("signup.html")

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = UserInfo.query.filter_by(UI_ID=request.form["UserID"]).first()
        if user: 
            if user.UI_WITHDRAWN is not None:
                print("탈퇴된 회원입니다.")
            elif check_password_hash(user.UI_PW, request.form["UserPW"]):
                print("로그인 성공!")
                session["user_id"] = user.UI_ID
                return redirect("/")
            else:
                print(f"로그인 실패: 암호 불 일치")
        else:
            print(f"로그인 실패: {request.form['UserID']}없음.")

    return render_template("login.html")


@app.route('/logout')
def logout():
    session.pop("user_id", None)
    return redirect("/")

@app.route("/room")
def room():
    user_id = session.get("user_id")
    if user_id is None:
        print("로그인 해주세요.")
        return redirect("/login")

    room_id = db.session.query(RoomMember.RI_ID).filter_by(UI_ID=user_id)
    my_room = RoomInfo.query.filter(RoomInfo.RI_ID.in_(room_id)).all()

    return render_template("room.html", rooms=my_room)

@app.route("/room/new", methods=["GET", "POST"])
def room_new():
    # 방 생성
    #ID, Name, Type, Max, Date
    user_id = session.get("user_id")
    if user_id is None:
        print("로그인 해주세요.")
        return redirect("/login")

    if request.method == "POST":
        room = RoomInfo(
            RI_NAME = request.form["user_name"], 
            RI_TYPE = request.form["type"], 
            RI_MAX = int(request.form["max"]), 
            RI_RDATE = date.today()
            
        )
        db.session.add(room)
        db.session.flush()

        print("방 생성 완료!")

        db.session.add(RoomMember(RI_ID=room.RI_ID, UI_ID=user_id))
        for uid in request.form.getlist("members"):
            db.session.add(RoomMember( RI_ID=room.RI_ID, UI_ID=uid ))
        
        db.session.commit()
        return redirect("/room")
    
    users = UserInfo.query.filter(
        UserInfo.UI_ID != user_id, 
        UserInfo.UI_WITHDRAWN.is_(None)
    ).all()
    
    return render_template("createRoom.html", users=users)


@app.route('/room/<int:room_id>')
def chatting(room_id):
    user_id = session.get("user_id")
    if user_id is None:
        print("로그인이 필요합니다.")
        return redirect("/login")
    if RoomMember.query.filter_by(RI_ID=room_id, UI_ID=user_id).first():
        messages = ChatMessage.query.filter_by(RI_ID=room_id).order_by(ChatMessage.CM_DATE).all()

        return render_template("chatting.html", room_id=room_id, messages=messages)
    return redirect("/room")




@app.route('/info')
def info():
    if session.get("user_id") is None:
        return redirect("/login")

    users = UserInfo.query.all()
    rooms = RoomInfo.query.all()
    names = {u.UI_ID: u.UI_NAME for u in users}

    members = {}
    for m in RoomMember.query.all():
        members.setdefault(m.RI_ID, []).append(m.UI_ID)

    return render_template("info.html", users=users, rooms=rooms, names=names, members=members)


@socketio.on("connect")
def handle_connect():
    print("Client Connect!!")


@socketio.on("join")
def handle_join(data):
    user_id = session.get("user_id")
    room_id = data["room_id"]
    if user_id is None:
        print("user 가 존재하지 않습니다.")
        return 
    if RoomMember.query.filter_by(RI_ID=room_id, UI_ID=user_id).first() is None:
        print("소속된 유저가 아닙니다.")
        return 
    join_room(str(room_id))

@socketio.on("send_message")
def handle_send_message(data):
    print(f"전달받은 메시지: {data}")

    # emit 으로 소켓 통신하는 사람들에게 data 를 뿌려주고
    # DB 에 저장하고

    user = session.get("user_id")
    room_id = data["room_id"]
    time = datetime.now()
    text = data["text"].strip()
    if user is None: 
        print("유저가 없음.")
        return
    if not text:
        print("빈 메시지")
        return
    if len(text) > 255:
        print("메시지 길이 초과")
        return
    if RoomMember.query.filter_by(UI_ID=user, RI_ID=room_id).first() is None:
        print("소속된 맴버가 아닙니다.")
        return


    message = ChatMessage(
        RI_ID = room_id, 
        UI_ID = user, 
        CM_MESSAGE = text, 
        CM_DATE = time
    )

    db.session.add(message)
    db.session.commit()
    
    emit("receive_message", {"time": time.strftime("%H:%M"), "user": user, "text": text}, room=str(room_id))





if __name__ == "__main__":
    socketio.run(app, debug=True, port=8080)

