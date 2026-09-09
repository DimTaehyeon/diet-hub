from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field

MEAL_TYPES = ["아침", "점심", "저녁", "간식"]


class FoodSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="검색어 (예: 김치)")


class FoodResponse(BaseModel):
    id: int
    name_ko: str
    category: Optional[str] = None
    kcal_per_serving: int

    class Config:
        from_attributes = True


class DietLogCreate(BaseModel):
    date: date
    meal_type: str = Field(..., description="아침/점심/저녁/간식")
    food_name: str = Field(..., min_length=1)
    kcal: int = Field(..., ge=0, le=5000)
    image_path: Optional[str] = None
    memo: Optional[str] = None


class DietLogUpdate(BaseModel):
    date: Optional[date] = None
    meal_type: Optional[str] = None
    food_name: Optional[str] = None
    kcal: Optional[int] = Field(default=None, ge=0, le=5000)
    image_path: Optional[str] = None
    memo: Optional[str] = None


class DietLogResponse(BaseModel):
    id: int
    date: date
    meal_type: str
    food_name: str
    kcal: int
    image_path: Optional[str] = None
    memo: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


def ok(data):
    return {"success": True, "data": data, "error": None}


def fail(message: str):
    return {"success": False, "data": None, "error": message}
