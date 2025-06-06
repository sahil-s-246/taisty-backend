from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
import datetime
Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    dish_id = Column(String, index=True)
    order_count = Column(Integer, default=1)
    feedback_score = Column(Float, default=0.0)
    last_ordered = Column(DateTime, default=datetime.datetime.utcnow)
