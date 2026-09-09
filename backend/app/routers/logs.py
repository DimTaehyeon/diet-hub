from datetime import date as date_cls
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..database import get_db
from ..models import DietLog
from ..schemas import DietLogCreate, DietLogUpdate, MEAL_TYPES, ok

router = APIRouter(prefix="/logs", tags=["logs"])


def _to_dict(log: DietLog):
    return {
        "id": log.id,
        "date": str(log.date),
        "meal_type": log.meal_type,
        "food_name": log.food_name,
        "kcal": log.kcal,
        "image_path": log.image_path,
        "memo": log.memo,
        "created_at": str(log.created_at) if log.created_at else None,
    }


@router.get("")
def get_logs(date: str, db: Session = Depends(get_db)):
    """?date=YYYY-MM-DD 일별 식단 조회"""
    try:
        d = date_cls.fromisoformat(date)
    except ValueError:
        raise HTTPException(status_code=400, detail="date 형식은 YYYY-MM-DD 여야 합니다.")
    logs = db.execute(select(DietLog).where(DietLog.date == d).order_by(DietLog.id)).scalars().all()
    items = [_to_dict(x) for x in logs]
    total_kcal = sum(x["kcal"] for x in items)
    return ok({"date": date, "total_kcal": total_kcal, "count": len(items), "items": items})


@router.post("")
def create_log(body: DietLogCreate, db: Session = Depends(get_db)):
    if body.meal_type not in MEAL_TYPES:
        raise HTTPException(status_code=400, detail=f"meal_type은 {MEAL_TYPES} 중 하나여야 합니다.")
    log = DietLog(
        date=body.date,
        meal_type=body.meal_type,
        food_name=body.food_name,
        kcal=body.kcal,
        image_path=body.image_path,
        memo=body.memo,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return ok(_to_dict(log))


@router.put("/{log_id}")
def update_log(log_id: int, body: DietLogUpdate, db: Session = Depends(get_db)):
    log = db.get(DietLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="해당 기록이 없습니다.")
    patch = body.model_dump(exclude_unset=True)
    if "meal_type" in patch and patch["meal_type"] not in MEAL_TYPES:
        raise HTTPException(status_code=400, detail=f"meal_type은 {MEAL_TYPES} 중 하나여야 합니다.")
    for k, v in patch.items():
        setattr(log, k, v)
    db.commit()
    db.refresh(log)
    return ok(_to_dict(log))


@router.delete("/{log_id}")
def delete_log(log_id: int, db: Session = Depends(get_db)):
    log = db.get(DietLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="해당 기록이 없습니다.")
    db.delete(log)
    db.commit()
    return ok({"deleted_id": log_id})
