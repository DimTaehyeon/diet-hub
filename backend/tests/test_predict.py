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

# 최소 PNG 1x1 (PIL 없이 바이트로 생성)
MIN_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c626001000000ffff0300000600055bf36d0000000049454e44ae426082"
)


def test_predict_fallback_no_model():
    """best.pt 학습 전: 폴백으로 직접입력 유도가 와야 함"""
    r = client.post("/api/predict", files={"image": ("test.png", io.BytesIO(MIN_PNG), "image/png")})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["success"] is True
    data = body["data"]
    assert "predictions" in data and len(data["predictions"]) >= 1
    assert data["need_manual_input"] is True
    assert data["image_id"].endswith(".png")


def test_predict_reject_non_image():
    r = client.post("/api/predict", files={"image": ("test.txt", io.BytesIO(b"hello"), "text/plain")})
    assert r.status_code == 400
