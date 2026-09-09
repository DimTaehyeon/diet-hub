# Backend 실행법

```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs
- 안드로이드 에뮬레이터에서는 `http://10.0.2.2:8000` 로 접속
- `.env.example` 복사해서 `.env` 생성 후 `DATABASE_URL` 수정

## PostgreSQL 운영 (Docker Desktop 설치 후)
```powershell
# 프로젝트 루트에서
docker compose up -d
# backend/.env 에 추가:
# DATABASE_URL=postgresql+psycopg://diet:dietpw@localhost:5432/dietdb
uvicorn app.main:app --reload --port 8000
# 테이블은 서버 시작 시 자동 생성. pytest는 인메모리 SQLite라 영향 없음.
```
