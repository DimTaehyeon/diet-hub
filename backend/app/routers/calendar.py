import calendar as calmod
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from ..database import get_db
from ..models import DietLog
from ..schemas import ok

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("")
def get_calendar(year: int, month: int, db: Session = Depends(get_db)):
    """?year=2026&month=09 -> 일자별 총kcal/건수"""
    if not (1 <= month <= 12):
        raise HTTPException(status_code=400, detail="month는 1~12여야 합니다.")
    _, last_day = calmod.monthrange(year, month)
    start = date(year, month, 1)
    end = date(year, month, last_day)
    rows = db.execute(
        select(DietLog.date, func.sum(DietLog.kcal), func.count(DietLog.id))
        .where(DietLog.date >= start, DietLog.date <= end)
        .group_by(DietLog.date)
    ).all()
    by_day = {str(r[0]): {"total_kcal": int(r[1] or 0), "count": int(r[2] or 0)} for r in rows}
    days = []
    for d in range(1, last_day + 1):
        key = str(date(year, month, d))
        info = by_day.get(key, {"total_kcal": 0, "count": 0})
        days.append({"date": key, **info})
    return ok({"year": year, "month": month, "days": days})
