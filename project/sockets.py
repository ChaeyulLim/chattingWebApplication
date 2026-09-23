from datetime import datetime
from flask import session
from flask_socketio import emit, join_room

from extensions import db, socketio
from models import ChatMessage, RoomMember


@socketio.on("connect")
def handle_connect():
    print("Client Connect!!")


@socketio.on("join")
def handle_join(data):
    user_id = session.get("user_id")
    room_id = data.get("room_id")
    if user_id is None:
        print("user 가 존재하지 않습니다.")
        return
    if room_id is None:
        print("room_id 가 없는 요청입니다.")
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
    room_id = data.get("room_id")
    time = datetime.now()
    text = data.get("text")
    if user is None:
        print("유저가 없음.")
        return
    if room_id is None:
        print("room_id 가 없는 요청입니다.")
        return
    if not isinstance(text, str) or not text.strip():
        print("빈 메시지")
        return
    text = text.strip()
    if len(text) > 255:
        print("메시지 길이 초과")
        return
    if RoomMember.query.filter_by(UI_ID=user, RI_ID=room_id).first() is None:
        print("소속된 맴버가 아닙니다.")
        return

    message = ChatMessage(
        RI_ID=room_id,
        UI_ID=user,
        CM_MESSAGE=text,
        CM_DATE=time
    )

    db.session.add(message)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        print("메시지 저장 중 오류가 발생했습니다.")
        return

    emit("receive_message", {
        "time": time.strftime("%H:%M"),
        "date": time.strftime("%Y.%m.%d"),
        "user": user,
        "user_name": session.get("user_name", user),
        "text": text
    }, room=str(room_id))
