from datetime import date
from flask import Blueprint, render_template, request, session, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db
from models import UserInfo, RoomMember

users_bp = Blueprint("users", __name__)


@users_bp.route('/')
def index():
    user_id = session.get("user_id")
    return render_template("index.html", user_id=user_id)


@users_bp.route('/signup', methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        existing_id = UserInfo.query.filter_by(UI_ID=request.form["UserID"]).first()

        if not request.form["UserID"].strip():
            flash("아이디를 입력해주세요.", "form_error")
        elif not request.form["UserPW"].strip():
            flash("비밀번호를 입력해주세요.", "form_error")
        elif not request.form["UserName"].strip():
            flash("이름을 입력해주세요.", "form_error")
        elif not request.form["UserMail"].strip():
            flash("메일을 입력해주세요.", "form_error")
        elif existing_id and existing_id.UI_WITHDRAWN is not None:
            flash("이미 사용했던 아이디입니다. 다른 아이디를 사용해주세요.", "form_error")
        elif existing_id:
            flash("이미 가입된 아이디 입니다.", "form_error")
        elif UserInfo.query.filter_by(UI_MAIL=request.form["UserMail"]).first():
            flash("이미 가입된 메일 입니다.", "form_error")
        else:
            user = UserInfo(
                UI_ID = request.form["UserID"],
                UI_PW = generate_password_hash(request.form["UserPW"]),
                UI_NAME = request.form["UserName"],
                UI_MAIL = request.form["UserMail"],
                UI_RDATE = date.today(),
            )
            db.session.add(user)
            try:
                db.session.commit()
            except Exception:
                db.session.rollback()
                flash("가입 중 오류가 발생했습니다. 다시 시도해주세요.", "form_error")
                return render_template("signup.html")

            flash("가입이 완료됐습니다. 로그인해 주세요.", "notice")
            return redirect("/login")

    return render_template("signup.html")


@users_bp.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = UserInfo.query.filter_by(UI_ID=request.form["UserID"]).first()
        if user:
            if user.UI_WITHDRAWN is not None:
                flash("탈퇴된 회원입니다.", "form_error")
            elif check_password_hash(user.UI_PW, request.form["UserPW"]):
                session["user_id"] = user.UI_ID
                session["user_name"] = user.UI_NAME
                return redirect("/")
            else:
                flash("아이디 또는 비밀번호가 일치하지 않습니다.", "form_error")
        else:
            flash("아이디 또는 비밀번호가 일치하지 않습니다.", "form_error")

    return render_template("login.html")


@users_bp.route('/logout')
def logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    return redirect("/")


@users_bp.route('/withdraw', methods=["GET", "POST"])
def withdraw():
    user_id = session.get("user_id")
    if user_id is None:
        flash("로그인이 필요합니다.", "notice")
        return redirect("/login")

    if request.method == "POST":
        user = UserInfo.query.filter_by(UI_ID=user_id).first()
        if user is None or user.UI_WITHDRAWN is not None:
            session.clear()
            flash("이미 탈퇴된 계정입니다.", "notice")
            return redirect("/login")

        if not check_password_hash(user.UI_PW, request.form["UserPW"]):
            flash("비밀번호가 일치하지 않습니다.", "form_error")
            return render_template("withdraw.html")

        user.UI_WITHDRAWN = date.today()
        RoomMember.query.filter_by(UI_ID=user_id).delete()

        try:
            db.session.commit()
        except Exception:
            db.session.rollback()
            flash("탈퇴 처리 중 오류가 발생했습니다. 다시 시도해주세요.", "form_error")
            return render_template("withdraw.html")

        session.clear()
        flash("탈퇴가 완료됐습니다. 그동안 이용해주셔서 감사합니다.", "notice")
        return redirect("/")

    return render_template("withdraw.html")
