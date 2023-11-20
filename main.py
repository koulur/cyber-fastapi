

from fastapi import FastAPI, Form, Request, Depends, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
# import secrets
from models import Base, User, engine, Message
from fastapi import status


from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import text


from pydantic import BaseModel
from typing import List


# SOLUTION 4
#from init_database import encrypt, decrypt


app = FastAPI()
templates = Jinja2Templates(directory="templates")


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, username: str = Cookie(None)):
    if username:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/logout")
def logout(response: Response):
    response.delete_cookie(key="username")
    return {"message": "Logged out"}


@app.post("/login")
async def login(response: Response, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return {"error": "try again"}
    # SOLUTION 3
    # REMEMBER TO USE THE SAME KEY AS GENERATED IN init_database.py
    # password = encrypt(password.encode(), key)
    if user and user.hashed_password == password:
        response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
        response.set_cookie(key="username", value=username, httponly=True)
        
        return response
        
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Cookie(None), db: Session = Depends(get_db)):
    
    if not username:
        return RedirectResponse(url="/")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return RedirectResponse(url="/")

    user_messages = db.query(Message).filter(
    (Message.author == user) |

    (Message.visible_to.contains(username))
    ).all()
    
    user_list = db.query(User).filter(User.username != username).all()
 
    return templates.TemplateResponse("dashboard.html", {"request": request, "messages": user_messages, "users": user_list})


#FLAW 1
@app.post("/post")
async def post_message(request: Request, message: str = Form(...), visible_to: List[str] = Form(...), username: str = Cookie(None)):

    if not username:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    with engine.connect() as con:
      
        conn = con.begin()
    
        result = con.execute(text("SELECT * FROM users WHERE username = :username"), {'username': username})
        author = result.first()
        if not author:
            conn.rollback()  # Rollback if user not found
            return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

        author_id = author['id'] if 'id' in author else author[0]

        visible_usernames = []
        for uname in visible_to:
            user_result = con.execute(text("SELECT * FROM users WHERE username = :username"), {'username': uname})
            user = user_result.first()
            if user:
                user_username = user['username'] if 'username' in user else user[1]
                visible_usernames.append(user_username)

        visible_to_str = ','.join(visible_usernames)
        con.execute(text("INSERT INTO messages (text, author_id, visible_to) VALUES (:text, :author_id, :visible_to)"),
                    {'text': message, 'author_id': author_id, 'visible_to': visible_to_str})

        conn.commit()  
     

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

# SOLUTTION 1
# @app.post("/post")
# async def post_message(request: Request, message: str = Form(...), visible_to: List[str] = Form(...), username: str = Cookie(None), db: Session = Depends(get_db)):
#     if not username:
#         return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

#     # Fetch the author user from the database
#     author = db.query(User).filter(User.username == username).first()
#     if not author:
#         return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
#     # Verify each username in the visible_to list
#     visible_usernames = []
#     for uname in visible_to:
#         user = db.query(User).filter(User.username == uname).first()
#         if user:
#             visible_usernames.append(user.username)

#     # Convert the list of verified usernames to a comma-separated string
#     visible_to_str = ','.join(visible_usernames)
#     new_message = Message(text=message, author_id=author.id, visible_to=visible_to_str)
#     db.add(new_message)
#     db.commit()
#     return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)


Base.metadata.create_all(bind=engine)
