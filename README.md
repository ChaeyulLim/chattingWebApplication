# 담소 - 웹 채팅 젝트

Flask + Flask-SocketIO로 만든 실시간 채팅 웹 애플리케이션입니다. 카카오톡을 참고해 1:1 대화와 그룹 채팅방, 실시간 메시지 수신을 지원하는 것을 목표로 만들었습니다.

## 주요 기능

- 회원가입 / 로그인 / 로그아웃 / 회원 탈퇴 (탈퇴한 아이디·메일은 재사용 불가)
- 1:1 채팅방 (상대방 1명만 선택, 이미 대화 중이면 기존 방으로 이동)
- 그룹 채팅방 (멤버 여러 명 선택, 개설 후 멤버 초대 / 나가기)
- Socket.IO 기반 실시간 메시지 송수신
- 채팅방 내 날짜 구분선 표시
- 로그인/회원가입 실패, 방 관련 안내 등 사용자 알림(토스트 / 인라인 에러)

## 기술 스택

- **Backend**: Python, Flask, Flask-SocketIO
- **DB / ORM**: PostgreSQL, Flask-SQLAlchemy, Flask-Migrate(Alembic)
- **Frontend**: Jinja2 템플릿, 바닐라 CSS/JavaScript, Socket.IO 클라이언트
- **환경 관리**: python-dotenv(`.env`)

## 프로젝트 구조

```
chatting_project/
├── docs/
│   ├── 개발일지.md         # 날짜별 개발 기록
│   └── 학습기술.md         # 새로 익힌 기술/개념 정리
├── project/
│   ├── app.py               # 진입점: 앱 생성, 설정, blueprint 등록, 실행
│   ├── extensions.py        # db / socketio / migrate 인스턴스
│   ├── models.py            # UserInfo, RoomInfo, RoomMember, ChatMessage
│   ├── users.py              # 회원가입 / 로그인 / 로그아웃 / 탈퇴
│   ├── rooms.py                # 방 목록 / 생성 / 입장 / 초대 / 나가기
│   ├── sockets.py               # 실시간 메시지 소켓 이벤트
│   ├── templates/                # 화면(Jinja2)
│   ├── static/                    # CSS
│   ├── migrations/                 # Flask-Migrate 마이그레이션
│   └── requirements.txt
└── README.md
```

## 실행 방법

```bash
cd project
python -m venv .venv
.venv\Scripts\Activate.ps1      # Windows PowerShell
pip install -r requirements.txt
```

PostgreSQL에 프로젝트 전용 데이터베이스를 만듭니다.

```sql
CREATE DATABASE chatting_db;
```

`project/.env` 파일을 만들고 아래 값을 채웁니다.

```
SECRET_KEY=원하는-비밀-문자열
DATABASE_URI=postgresql+psycopg2://postgres:암호@localhost:5432/chatting_db
```

DB 초기화 후 서버를 실행합니다.

```bash
flask --app app db upgrade
python app.py
```

기본적으로 `http://127.0.0.1:8080`에서 접속할 수 있습니다.

## 개발 방식

전체 기획과 설계(데이터 모델링, 기능 흐름, 화면 구조 등)는 직접 진행했습니다. AI(Claude)는 아래 용도로 활용했습니다.

- 프론트엔드 화면/스타일 구현
- 여러 계정으로 로그인·방 생성·초대·탈퇴 등 실제 시나리오를 따라가며 기능 검증
- 잘 모르는 기술/개념을 찾아보고 학습하는 용도

개발 과정과 배운 내용은 [docs/개발일지.md](docs/개발일지.md), [docs/학습기술.md](docs/학습기술.md)에 정리되어 있습니다.
