"""P5 E2E: 촬영 업로드 -> 예측 -> 저장(수정) -> 일별조회 -> 캘린더 -> 삭제"""
import io
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Food

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
db = TestingSession()
if not db.query(Food).first():
    db.add(Food(name_ko="김치찌개", category="한식", kcal_per_serving=590))
    db.commit()
db.close()

client = TestClient(app)
MIN_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c626001000000ffff0300000600055bf36d0000000049454e44ae426082"
)


def test_e2e_full_flow():
    # 1. 촬영 업로드 -> 예측 (학습 전이므로 폴백 + 수동입력 플래그)
    r = client.post("/api/predict", files={"image": ("meal.png", io.BytesIO(MIN_PNG), "image/png")})
    assert r.status_code == 200, r.text
    pred = r.json()["data"]
    assert pred["need_manual_input"] is True
    image_path = pred["image_path"]

    # 2. 사용자가 메뉴 수정해서 저장 (김치찌개 1인분)
    r = client.post("/api/logs", json={
        "date": "2026-09-09", "meal_type": "점심",
        "food_name": "김치찌개", "kcal": 590,
        "image_path": image_path, "memo": "E2E 테스트",
    })
    assert r.status_code == 200, r.text
    log_id = r.json()["data"]["id"]

    # 3. 일별 조회에 방금 저장이 보여야 함
    r = client.get("/api/logs", params={"date": "2026-09-09"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["count"] >= 1 and data["total_kcal"] >= 590
    assert any(i["id"] == log_id for i in data["items"])

    # 4. 캘린더 월 조회에 집계되어야 함
    r = client.get("/api/calendar", params={"year": 2026, "month": 9})
    assert r.status_code == 200
    days = {d["date"]: d for d in r.json()["data"]["days"]}
    assert days["2026-09-09"]["count"] >= 1

    # 5. 삭제 후 일별 조회에서 사라져야 함
    r = client.delete(f"/api/logs/{log_id}")
    assert r.status_code == 200
    r = client.get("/api/logs", params={"date": "2026-09-09"})
    assert all(i["id"] != log_id for i in r.json()["data"]["items"])


def test_cors_headers_present():
    """Flutter 웹/에뮬레이터 접속용 CORS 헤더 확인"""
    r = client.options(
        "/api/logs",
        headers={"Origin": "http://localhost", "Access-Control-Request-Method": "GET"},
    )
    # 미들웨어가 살아있으면 200 계열 + allow-origin 헤더
    # (allow_credentials=True면 Starlette가 Origin을 에코하므로 * 또는 요청 Origin 모두 허용)
    assert r.status_code in (200, 204)
    assert r.headers.get("access-control-allow-origin") in ("*", "http://localhost")
