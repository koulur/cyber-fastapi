from models import User, Message  # Import your models
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./test.db"  # Ensure this matches your database URL
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def view_data():
    db = SessionLocal()
    users = db.query(User).all()
    messages = db.query(Message).all()

    print("Users:")
    for user in users:
        print(f"{user.id} - {user.username} - {user.hashed_password}")

    print("\nMessages:")
    for message in messages:
        print(f"{message.id} - {message.text} - Author ID: {message.author_id} - Visible To: {message.visible_to}")

    db.close()

if __name__ == "__main__":
    view_data()
