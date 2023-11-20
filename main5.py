from fastapi import FastAPI, Form, Request, Depends, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
# import secrets
from models import Base, User, engine, Message
from fastapi import status

import json


from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import text


from pydantic import BaseModel
from typing import List

import secrets


app = FastAPI()
templates = Jinja2Templates(directory="templates")

session_store = {}

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, username: str = Cookie(None)):
    return templates.TemplateResponse("index.html", {"request": request})
   


@app.get("/logout")
def logout(response: Response):
    response.delete_cookie(key="session_token")
    response.delete_cookie(key="username")
    return {"message": "Logged out"}



@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Cookie(None), db: Session = Depends(get_db)):
   
    session_token = request.cookies.get("session_token")
    if not session_token or session_token not in session_store:

        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    username = session_store[session_token]
    user = db.query(User).filter(User.username == username).first()
    if not user:

        return RedirectResponse(url="/")

    user_messages = db.query(Message).filter(
    (Message.author == user) |

    (Message.visible_to.contains(username))
    ).all()

    user_list = db.query(User).filter(User.username != username).all()
   
    return templates.TemplateResponse("dashboard.html", {"request": request, "messages": user_messages, "users": user_list})



@app.post("/post")
async def post_message(request: Request, message: str = Form(...), visible_to: List[str] = Form(...), username: str = Cookie(None)):
    session_token = request.cookies.get("session_token")
    if not session_token or session_token not in session_store:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    username = session_store[session_token]

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


Base.metadata.create_all(bind=engine)

# FLAW 5
# Internals of session storage being leaked.
@app.post("/login")
async def login(response: Response, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):

    user = db.query(User).filter(User.username == username).first()
    # The problem is here
    if not (user and user.hashed_password == password): 
        return {"Could not find the user/password you were looking for. Perhaps you meant to type:": json.dumps(session_store)}

  
    session_token = secrets.token_urlsafe()
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="session_token", value=session_token, httponly=True, secure=True)
    

    session_store[session_token] = user.username  # Storing username for simplicity

    return response