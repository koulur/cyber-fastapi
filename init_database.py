from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import Base, User 
from models import Base, User, Message, engine

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)



# SOLUTION 3
from cryptography.fernet import Fernet

key = Fernet.generate_key()  # store in a secure location

def encrypt(message: bytes, key: bytes) -> bytes:
    return Fernet(key).encrypt(message)
    
def decrypt(token: bytes, key: bytes) -> bytes:
    return Fernet(key).decrypt(token)


# FLAW 
def initialise():
    Base.metadata.create_all(bind=engine)  
    db = SessionLocal()
    try:
        # dummy users
        password1= "first"
        password2="second"
        password3="third"
        #SOLUTION 3
        # REMINDER - you have to create the key first.
        # password1 = encrypt(password1.encode(), key)
        # password2 = encrypt(password2.encode(), key)
        # password3 = encrypt(password3.encode(), key)
        user1 = User(username="first",hashed_password=password1)
        user2 = User(username="second",hashed_password=password2)
        user3 = User(username="third",hashed_password=password3)
        db.add(user1)
        db.add(user2)
        db.add(user3)
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    initialise()
