# Backend 실행법

```powershell
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

- Swagger UI: http://127.0.0.1:8000/docs
- 안드로이드 에뮬레이터에서는 `http://10.0.2.2:8000` 로 접속
- `.env.example` 복사해서 `.env` 생성 후 `DATABASE_URL` 수정
