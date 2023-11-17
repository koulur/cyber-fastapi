from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import Base, User 
from models import Base, User, Message, engine

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def initialise():
    Base.metadata.create_all(bind=engine)  
    db = SessionLocal()
    try:
        # Create dummy users
        # user1 = User(username="first", hashed_password="first")
        user1 = User(username="first",hashed_password="first")
        user2 = User(username="second",hashed_password="second")
        user3 = User(username="third",hashed_password="third")
        db.add(user1)
        db.add(user2)
        db.add(user3)
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    initialise()
