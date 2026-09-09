from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from .database import Base, engine, SessionLocal
from .models import Food
from .routers import foods, logs, calendar, predict
from pathlib import Path

# 초기 22개 메뉴 + 1인분 kcal
SEED_FOODS = [
    ("김치찌개", "한식", 590), ("된장찌개", "한식", 420), ("비빔밥", "한식", 720),
    ("불고기", "한식", 650), ("삼겹살", "한식", 820), ("후라이드치킨", "양식", 900),
    ("양념치킨", "양식", 1000),
    ("피자", "양식", 850), ("햄버거", "양식", 700), ("라면", "분식", 550),
    ("김밥", "분식", 480), ("떡볶이", "분식", 620), ("삼계탕", "한식", 780),
    ("냉면", "한식", 540), ("짜장면", "중식", 750), ("짬뽕", "중식", 680),
    ("초밥", "일식", 560), ("샐러드", "양식", 280), ("계란후라이", "한식", 180),
    ("밥", "한식", 300), ("국수", "한식", 520), ("탕수육", "중식", 650),
]


def seed_foods():
    db = SessionLocal()
    try:
        count = db.execute(select(Food)).scalars().first()
        if count is None:
            for name, cat, kcal in SEED_FOODS:
                db.add(Food(name_ko=name, category=cat, kcal_per_serving=kcal))
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_foods()
    # 모델 1회 프리로드 체크 (torch 없어도 서버는 정상 기동, 폴백 모드)
    best = Path(__file__).resolve().parents[3] / "ai" / "models" / "best.pt"
    app.state.model_loaded = best.exists()
    try:
        import torch  # noqa: F401
        app.state.torch_available = True
    except Exception:
        app.state.torch_available = False
    print(f"[predict] model_loaded={app.state.model_loaded} torch={app.state.torch_available}")
    yield


app = FastAPI(title="식단 관리 API", version="0.2.0 (P3 predict)", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용. 운영에서는 Flutter 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(foods.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(calendar.router, prefix="/api")
app.include_router(predict.router, prefix="/api")


@app.get("/", tags=["health"])
def root():
    return {"success": True, "data": {"message": "식단 관리 API 동작 중. /docs 에서 테스트하세요."}, "error": None}


@app.get("/health", tags=["health"])
def health():
    return {"success": True, "data": {"status": "ok"}, "error": None}
