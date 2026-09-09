# API 명세 (P3)

모든 응답: `{ success, data, error }`

- `POST /api/foods/search` {query} → 메뉴 TOP20
- `GET /api/foods` → 전체 메뉴 (100개)
- `GET /api/logs?date=YYYY-MM-DD` → {date, total_kcal, count, items[]}
- `POST /api/logs` {date, meal_type, food_name, kcal, image_path?, memo?}
- `PUT /api/logs/{id}` → 부분 수정
- `DELETE /api/logs/{id}`
- `GET /api/calendar?year=2026&month=09` → {year, month, days[{date, total_kcal, count}]}
- `POST /api/predict` multipart `image` → {predictions[{label, confidence, kcal}], image_id, image_path, need_manual_input, model_loaded}
  - 예: `curl -X POST http://127.0.0.1:8000/api/predict -F "image=@Cfg.jpg"`
  - confidence < 0.5 또는 모델 없으면 need_manual_input=true + label "직접입력 필요"
- `GET /health`, `GET /`

meal_type: 아침/점심/저녁/간식
