from sqlalchemy import Column, Integer, String, Date, DateTime, func
from .database import Base


class Food(Base):
    __tablename__ = "foods"

    id = Column(Integer, primary_key=True, index=True)
    name_ko = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), nullable=True)
    kcal_per_serving = Column(Integer, nullable=False)


class DietLog(Base):
    __tablename__ = "diet_logs"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, index=True)
    meal_type = Column(String(20), nullable=False)  # 아침/점심/저녁/간식
    food_name = Column(String(100), nullable=False)
    kcal = Column(Integer, nullable=False)
    image_path = Column(String(255), nullable=True)
    memo = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
