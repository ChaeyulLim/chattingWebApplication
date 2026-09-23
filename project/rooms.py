from datetime import date
from flask import Blueprint, render_template, request, session, redirect, flash

from extensions import db
from models import UserInfo, RoomInfo, RoomMember, ChatMessage

rooms_bp = Blueprint("rooms", __name__)


def _display_name(room, viewer_id, member_ids, names):
    if room.RI_TYPE == "D":
        other = next((uid for uid in member_ids if uid != viewer_id), None)
        if other:
            return names.get(other, other)
    return room.RI_NAME or "(이름 없음)"


def _find_existing_dm(user_id, partner_id):
    my_rooms = db.session.query(RoomMember.RI_ID).filter_by(UI_ID=user_id)
    return (
        db.session.query(RoomMember.RI_ID)
        .join(RoomInfo, RoomInfo.RI_ID == RoomMember.RI_ID)
        .filter(RoomInfo.RI_TYPE == "D", RoomMember.UI_ID == partner_id)
        .filter(RoomMember.RI_ID.in_(my_rooms))
        .first()
    )


@rooms_bp.route("/room")
def room():
    user_id = session.get("user_id")
    if user_id is None:
        flash("로그인이 필요합니다.", "notice")
        return redirect("/login")

    room_id = db.session.query(RoomMember.RI_ID).filter_by(UI_ID=user_id)
    my_room = RoomInfo.query.filter(RoomInfo.RI_ID.in_(room_id)).all()

    room_members = {}
    for m in RoomMember.query.filter(RoomMember.RI_ID.in_([r.RI_ID for r in my_room])).all():
        room_members.setdefault(m.RI_ID, []).append(m.UI_ID)

    names = {u.UI_ID: u.UI_NAME for u in UserInfo.query.all()}
    member_counts = {rid: len(uids) for rid, uids in room_members.items()}
    display_names = {
        r.RI_ID: _display_name(r, user_id, room_members.get(r.RI_ID, []), names)
        for r in my_room
    }

    return render_template(
        "room.html",
        rooms=my_room,
        member_counts=member_counts,
        display_names=display_names
    )


@rooms_bp.route("/room/new", methods=["GET", "POST"])
def room_new():
    # 방 생성
    #ID, Name, Type, Date
    user_id = session.get("user_id")
    if user_id is None:
        flash("로그인이 필요합니다.", "notice")
        return redirect("/login")

    if request.method == "POST":
        room_type = request.form["type"]
        member_ids = request.form.getlist("members")

        if room_type == "D":
            if len(member_ids) != 1:
                flash("1:1 방은 상대방을 한 명만 선택해야 합니다.", "form_error")
                return redirect("/room/new")

            partner_id = member_ids[0]
            existing_room_id = _find_existing_dm(user_id, partner_id)
            if existing_room_id:
                flash("이미 대화 중인 1:1 방으로 이동합니다.", "notice")
                return redirect(f"/room/{existing_room_id[0]}")

            room = RoomInfo(RI_NAME=None, RI_TYPE="D", RI_RDATE=date.today())

        elif room_type == "G":
            if len(member_ids) < 1:
                flash("멤버를 최소 1명 이상 선택해주세요.", "form_error")
                return redirect("/room/new")

            room = RoomInfo(
                RI_NAME = request.form["user_name"],
                RI_TYPE = "G",
                RI_RDATE = date.today()
            )
        else:
            flash("올바르지 않은 방 종류입니다.", "form_error")
            return redirect("/room/new")

        db.session.add(room)
        db.session.flush()

        db.session.add(RoomMember(RI_ID=room.RI_ID, UI_ID=user_id))
        for uid in member_ids:
            db.session.add(RoomMember( RI_ID=room.RI_ID, UI_ID=uid ))

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("방 생성 중 오류가 발생했습니다. 다시 시도해주세요.", "notice")
            return redirect("/room/new")

        flash("방을 만들었습니다.", "notice")
        return redirect("/room")

    users = UserInfo.query.filter(
        UserInfo.UI_ID != user_id,
        UserInfo.UI_WITHDRAWN.is_(None)
    ).all()

    return render_template("createRoom.html", users=users)


@rooms_bp.route('/room/<int:room_id>')
def chatting(room_id):
    user_id = session.get("user_id")
    if user_id is None:
        flash("로그인이 필요합니다.", "notice")
        return redirect("/login")
    if RoomMember.query.filter_by(RI_ID=room_id, UI_ID=user_id).first():
        room = RoomInfo.query.filter_by(RI_ID=room_id).first()
        messages = ChatMessage.query.filter_by(RI_ID=room_id).order_by(ChatMessage.CM_DATE).all()
        names = {u.UI_ID: u.UI_NAME for u in UserInfo.query.all()}
        member_ids = [m.UI_ID for m in RoomMember.query.filter_by(RI_ID=room_id).all()]
        room_name = _display_name(room, user_id, member_ids, names)

        return render_template(
            "chatting.html",
            room_id=room_id,
            room=room,
            room_name=room_name,
            messages=messages,
            names=names,
            member_count=len(member_ids)
        )

    flash("참여 중인 방이 아닙니다.", "notice")
    return redirect("/room")


@rooms_bp.route('/room/<int:room_id>/invite', methods=["GET", "POST"])
def invite(room_id):
    user_id = session.get("user_id")
    if user_id is None:
        flash("로그인이 필요합니다.", "notice")
        return redirect("/login")

    room = RoomInfo.query.filter_by(RI_ID=room_id).first()
    if room is None or RoomMember.query.filter_by(RI_ID=room_id, UI_ID=user_id).first() is None:
        flash("참여 중인 방이 아닙니다.", "notice")
        return redirect("/room")

    if room.RI_TYPE != "G":
        flash("1:1 방에는 인원을 추가할 수 없습니다.", "notice")
        return redirect(f"/room/{room_id}")

    existing_ids = [m.UI_ID for m in RoomMember.query.filter_by(RI_ID=room_id).all()]

    if request.method == "POST":
        candidates = UserInfo.query.filter(
            UserInfo.UI_ID.notin_(existing_ids),
            UserInfo.UI_WITHDRAWN.is_(None)
        ).all()
        valid_ids = {u.UI_ID for u in candidates}

        added = 0
        for uid in request.form.getlist("members"):
            if uid not in valid_ids:
                continue
            db.session.add(RoomMember(RI_ID=room_id, UI_ID=uid))
            added += 1

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("초대 중 오류가 발생했습니다. 다시 시도해주세요.", "notice")
            return redirect(f"/room/{room_id}/invite")

        flash(f"{added}명을 초대했습니다." if added else "추가된 인원이 없습니다.", "notice")
        return redirect(f"/room/{room_id}")

    users = UserInfo.query.filter(
        UserInfo.UI_ID.notin_(existing_ids),
        UserInfo.UI_WITHDRAWN.is_(None)
    ).all()

    return render_template("inviteMembers.html", room=room, users=users)


@rooms_bp.route('/room/<int:room_id>/leave', methods=["POST"])
def leave(room_id):
    user_id = session.get("user_id")
    if user_id is None:
        flash("로그인이 필요합니다.", "notice")
        return redirect("/login")

    membership = RoomMember.query.filter_by(RI_ID=room_id, UI_ID=user_id).first()
    if membership is None:
        flash("참여 중인 방이 아닙니다.", "notice")
        return redirect("/room")

    db.session.delete(membership)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("방을 나가는 중 오류가 발생했습니다. 다시 시도해주세요.", "notice")
        return redirect(f"/room/{room_id}")

    flash("방을 나갔습니다.", "notice")
    return redirect("/room")


@rooms_bp.route('/info')
def info():
    if session.get("user_id") is None:
        flash("로그인이 필요합니다.", "notice")
        return redirect("/login")

    users = UserInfo.query.all()
    rooms = RoomInfo.query.all()
    names = {u.UI_ID: u.UI_NAME for u in users}

    members = {}
    for m in RoomMember.query.all():
        members.setdefault(m.RI_ID, []).append(m.UI_ID)

    return render_template("info.html", users=users, rooms=rooms, names=names, members=members)
