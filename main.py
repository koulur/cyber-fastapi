from fastapi import FastAPI, Form, Request, Depends, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
# import secrets
from models import Base, User, engine, Message
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import create_engine
from fastapi import status
from sqlalchemy import text


from pydantic import BaseModel
from typing import List


app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Dummy database
# users = {"first": "first", "second": "second", "third": "third"}
# messages = []
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

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, username: str = Cookie(None)):
    print(username)
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
    if user and user.hashed_password == password:
        print(f"cookie being set: {username}")
        response.set_cookie(key="username", value=username, httponly=True, max_age=1800)
        # return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
        return {"message": "Go manually dumbo"}

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Cookie(None), db: Session = Depends(get_db)):
    if not username:
        return RedirectResponse(url="/")
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
    print([userr.username for userr in user_list])

    print(user_list)
    return templates.TemplateResponse("dashboard.html", {"request": request, "messages": user_messages, "users": user_list})



@app.post("/post")
async def post_message(request: Request, message: str = Form(...), visible_to: List[str] = Form(...), username: str = Cookie(None)):
    if not username:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    with engine.connect() as con:
        # Explicitly begin a transaction
        trans = con.begin()
    
        result = con.execute(text("SELECT * FROM users WHERE username = :username"), {'username': username})
        author = result.first()
        if not author:
            trans.rollback()  # Rollback if user not found
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

        trans.commit()  # Commit the transaction
     

    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

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
#         print(user)
#         if user:
#             print(f'User: {user}, username: {user.username}')
#             visible_usernames.append(user.username)

#     # Convert the list of verified usernames to a comma-separated string
#     visible_to_str = ','.join(visible_usernames)
#     print(f'visible_to_str {visible_to_str}')
#     new_message = Message(text=message, author_id=author.id, visible_to=visible_to_str)
#     db.add(new_message)
#     db.commit()
#     return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)



Base.metadata.create_all(bind=engine)
