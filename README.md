# 식단 관리 앱

핸드폰 카메라 → AI 음식 분류 → 칼로리 + 캘린더 기록 앱 (MVP)

## 구조
- `backend/` : FastAPI + SQLAlchemy (P1+P3 완료, 테스트 7개)
- `ai/` : P2 학습 파이프라인 완료 (best.pt 학습만 남음)
- `frontend/` : P4 Flutter 3화면 완료 (SDK 설치 후 run)
- `docs/` : API 명세 + DEMO 체크리스트

## 백엔드 실행 (초보자용)
```powershell
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Swagger: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health
- 안드로이드 에뮬레이터는 `http://10.0.2.2:8000` 으로 접속 (상세 `docs/DEMO.md`)

## 테스트
```powershell
cd backend
pytest -v
```

## curl 예제
```powershell
# 메뉴 검색
curl -X POST http://127.0.0.1:8000/api/foods/search -H "Content-Type: application/json" -d '{"query":"김치"}'
# 식단 저장
curl -X POST http://127.0.0.1:8000/api/logs -H "Content-Type: application/json" -d '{"date":"2026-09-09","meal_type":"점심","food_name":"김치찌개","kcal":590}'
# 일별 조회
curl "http://127.0.0.1:8000/api/logs?date=2026-09-09"
# 캘린더 조회
curl "http://127.0.0.1:8000/api/calendar?year=2026&month=09"
# 이미지 예측 (meal.jpg 경로 수정)
curl -X POST http://127.0.0.1:8000/api/predict -F "image=@meal.jpg"
```

## 프론트 실행
```powershell
cd frontend
flutter pub get
flutter run
```
