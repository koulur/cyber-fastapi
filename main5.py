

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

# SOLUTION 2
session_store = {}

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# def get_current_user(username: str = Cookie(None)):
#     if username in users:
#         return username
#     return None


# SOLUTION 2
def authenticate_user(username: str, password: str):
    # Dummy implementation for demonstration
    # In a real application, you should verify the username and password
    # with your database and return user details if authentication is successful
    user = db.query(User).filter(User.username == username).first()
    if user and user.verify_password(password):
        return user
    return None

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, username: str = Cookie(None)):
    print(username)
    if username:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/logout")
def logout(response: Response):
    response.delete_cookie(key="session_token")
    response.delete_cookie(key="username")
    return {"message": "Logged out"}



# FLAW 4
# Internals of session storage being leaked.
@app.post("/login")
async def login(response: Response, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):

    # If you're also looking at FLAW 3, remember to encrypt/decrypt password
    user = db.query(User).filter(User.username == username).first()
    if not (user and user.hashed_password == password):
        print(session_store)
        return {"Could not find the user/password you were looking for. Perhaps you meant to type:": json.dumps(session_store)}

  
    session_token = secrets.token_urlsafe()
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="session_token", value=session_token, httponly=True, secure=True)
    
    # SOLUTION 2
    # Store the session token with user info in the session store
    session_store[session_token] = user.username  # Storing username for simplicity

    return response
   
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Cookie(None), db: Session = Depends(get_db)):
    # if not username:
    #     return RedirectResponse(url="/")
    
    session_token = request.cookies.get("session_token")
    if not session_token or session_token not in session_store:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    username = session_store[session_token]
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return RedirectResponse(url="/")

    
    # print(f'Username in dash: {username}')
    user_messages = db.query(Message).filter(
    (Message.author == user) |

    (Message.visible_to.contains(username))
    ).all()
    for message in user_messages:
        # Check if the author object and username are populated
        if message.author and message.author.username:
            print(f"Message: {message.text} - Author: {message.author.username}")
        else:
            print(f"Message: {message.text} has no author with a username")
    user_list = db.query(User).filter(User.username != username).all()
    # print([userr.username for userr in user_list])

    # print(user_list)
    # SOLUTION 2
   
    # FLAW 2
    return templates.TemplateResponse("dashboard.html", {"request": request, "messages": user_messages, "users": user_list})


#FLAW 1
@app.post("/post")
async def post_message(request: Request, message: str = Form(...), visible_to: List[str] = Form(...), username: str = Cookie(None)):
    session_token = request.cookies.get("session_token")
    if not session_token or session_token not in session_store:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    username = session_store[session_token]
    print("posting")
    if not username:
        print("rediredctitntoioitj")
        print(username)
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    with engine.connect() as con:
      
        conn = con.begin()
    
        result = con.execute(text("SELECT * FROM users WHERE username = :username"), {'username': username})
        author = result.first()
        if not author:
            print("No author")
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
    print("going with session cookie")
    return {"you": "have to go manually.."}
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
#     print(f'visiii: {visible_to}')
#     # Verify each username in the visible_to list
#     visible_usernames = []
#     for uname in visible_to:
#         user = db.query(User).filter(User.username == uname).first()
#         if user:
#             print(f'User: {user}, username: {user.username}')
#             visible_usernames.append(user.username)

#     # Convert the list of verified usernames to a comma-separated string
#     visible_to_str = ','.join(visible_usernames)
#     new_message = Message(text=message, author_id=author.id, visible_to=visible_to_str)
#     db.add(new_message)
#     db.commit()
#     return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)



Base.metadata.create_all(bind=engine)
