# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from models import Order, Base

DATABASE_URL = "sqlite:///./tAISTy.db"  # Replace with your actual DB URI

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})  # For SQLite
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



# Create tables before using them
Base.metadata.create_all(engine)


# Dependency to inject DB session into routes
def get_db():
    db: Session = SessionLocal()
    try:
        # This code will run each time get_db is called - likely not what you want
        orders = [
            Order(user_id="user_123", dish_id="Paneer Tikka", order_count=2, feedback_score=4.0),
            Order(user_id="user_123", dish_id="Chole Bhature", order_count=1, feedback_score=3.5),
            Order(user_id="user_456", dish_id="Paneer Tikka", order_count=3, feedback_score=5.0),
            Order(user_id="user_456", dish_id="Butter Chicken", order_count=2, feedback_score=4.5),
            Order(user_id="user_789", dish_id="Masala Dosa", order_count=1, feedback_score=4.0),
            Order(user_id="user_789", dish_id="Chole Bhature", order_count=2, feedback_score=4.0),
            Order(user_id="user_789", dish_id="Paneer Tikka", order_count=1, feedback_score=3.0),
        ]

        db.add_all(orders)
        db.commit()
        yield db
    finally:
        db.close()
from sqlalchemy import inspect
inspector = inspect(engine)
print("Tables in database:", inspector.get_table_names())