# P5 통합 데모 체크리스트

## 검증 완료 (2026-09-09)
- `pytest -v` : 7 passed (crud 3 + predict 2 + e2e 2)
- 실서버 기동 (`uvicorn app.main:app --port 8009`) : /health, /api/foods/search, /api/calendar 200 OK
- CORS : OPTIONS /api/logs → allow-origin 헤더 확인 (Credentials 모드라 Origin 에코)
- E2E 흐름 : predict 업로드 → logs 저장 → 일별 조회 → calendar 집계 → 삭제, TestClient로 전구간 통과
- lifespan : `model_loaded=False torch=False` (학습 전 폴백 모드, 서버 정상 기동)

## 데모 실행 (backend + flutter run 만으로 가능)
```powershell
# 터미널 1: 백엔드 (실기기 접속이면 --host 0.0.0.0)
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# http://127.0.0.1:8000/docs 확인

# 터미널 2: 프론트 (Flutter SDK 설치 후)
cd frontend
flutter pub get
flutter run                                    # 안드로이드 에뮬레이터 (10.0.2.2 자동)
flutter run --dart-define=API_BASE=http://127.0.0.1:8000 -d chrome   # PC 크롬
```

## curl 예제 3개
```powershell
curl -X POST http://127.0.0.1:8000/api/foods/search -H "Content-Type: application/json" -d '{"query":"김치"}'
curl -X POST http://127.0.0.1:8000/api/logs -H "Content-Type: application/json" -d '{"date":"2026-09-09","meal_type":"점심","food_name":"김치찌개","kcal":590}'
curl "http://127.0.0.1:8000/api/calendar?year=2026&month=09"
curl -X POST http://127.0.0.1:8000/api/predict -F "image=@meal.jpg"
```

## 현재 한계 (솔직 기록)
- `ai/models/best.pt` 없음 → predict는 "직접입력 필요" 폴백. P2 데이터 수집+학습 후 자동 실측 전환
- PC에 Flutter SDK / torch 미설치 → 프론트 실기동·모델 학습은 사용자 PC에서 실행 필요
- uploads/*.jpg, *.db는 git 제외 권장 (.gitignore 추가 예정)
