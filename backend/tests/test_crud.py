from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app, seed_foods
from app.models import Food

# 인메모리 테스트 DB
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
# 테스트 DB에 초기 메뉴 시드
db = TestingSession()
if not db.query(Food).first():
    for name, cat, kcal in [("김치찌개", "한식", 590), ("비빔밥", "한식", 720)]:
        db.add(Food(name_ko=name, category=cat, kcal_per_serving=kcal))
    db.commit()
db.close()

client = TestClient(app)


def test_food_search():
    r = client.post("/api/foods/search", json={"query": "김치"})
    assert r.status_code == 200
    body = r.json()
    assert body["success"] is True
    assert any("김치" in f["name_ko"] for f in body["data"])


def test_log_crud_flow():
    # 생성
    r = client.post("/api/logs", json={
        "date": "2026-09-09", "meal_type": "점심",
        "food_name": "김치찌개", "kcal": 590, "memo": "테스트"
    })
    assert r.status_code == 200, r.text
    log_id = r.json()["data"]["id"]

    # 일별 조회
    r = client.get("/api/logs", params={"date": "2026-09-09"})
    assert r.status_code == 200
    assert r.json()["data"]["total_kcal"] >= 590

    # 수정
    r = client.put(f"/api/logs/{log_id}", json={"kcal": 600})
    assert r.status_code == 200
    assert r.json()["data"]["kcal"] == 600

    # 캘린더 조회
    r = client.get("/api/calendar", params={"year": 2026, "month": 9})
    assert r.status_code == 200
    days = r.json()["data"]["days"]
    assert any(d["date"] == "2026-09-09" and d["count"] >= 1 for d in days)

    # 삭제
    r = client.delete(f"/api/logs/{log_id}")
    assert r.status_code == 200
    assert r.json()["data"]["deleted_id"] == log_id


def test_invalid_meal_type():
    r = client.post("/api/logs", json={
        "date": "2026-09-09", "meal_type": "브런치",
        "food_name": "밥", "kcal": 300
    })
    assert r.status_code == 400
