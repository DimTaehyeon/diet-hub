from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..database import get_db
from ..models import Food
from ..schemas import FoodSearchRequest, ok

router = APIRouter(prefix="/foods", tags=["foods"])


@router.post("/search")
def search_foods(body: FoodSearchRequest, db: Session = Depends(get_db)):
    q = f"%{body.query.strip()}%"
    foods = db.execute(select(Food).where(Food.name_ko.like(q)).limit(20)).scalars().all()
    data = [
        {"id": f.id, "name_ko": f.name_ko, "category": f.category, "kcal_per_serving": f.kcal_per_serving}
        for f in foods
    ]
    return ok(data)


@router.get("")
def list_foods(db: Session = Depends(get_db)):
    foods = db.execute(select(Food).order_by(Food.name_ko).limit(100)).scalars().all()
    data = [
        {"id": f.id, "name_ko": f.name_ko, "category": f.category, "kcal_per_serving": f.kcal_per_serving}
        for f in foods
    ]
    return ok(data)
