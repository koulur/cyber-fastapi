from fastapi import FastAPI, Form, Request, Depends, Response, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import secrets

from fastapi import status


from pydantic import BaseModel
from typing import List, Optional
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Dummy database
users = {"first": "first", "second": "second", "third": "third"}
messages = []

class Message:
    def __init__(self, text: str, visible_to: list, author: str):
        self.text = text
        self.visible_to = visible_to
        self.author = author

def get_current_user(username: str = Cookie(None)):
    if username in users:
        return username
    return None

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
async def login(response: Response, username: str = Form(...), password: str = Form(...)):
    if username in users and users[username] == password:
        print(f"cookie being set: {username}")
        # response.
        response.set_cookie(key="username", value=username, httponly=True, max_age=1800)
        return {"message": "Cookie set, please navigate to /dashboard manually."}

        # return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    print("no cookie set")
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, username: str = Cookie(None)):
    print(f'username in dashboard: {username}')
    if not username or username not in users:
        # Redirect to login if not authenticated
        print(f'no username in /dashboard {username}')
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    user_messages = [msg for msg in messages if username in msg.visible_to or msg.author == username]
    user_list = [user for user in users if user != username]
    return templates.TemplateResponse("dashboard.html", {"request": request, "messages": user_messages, "users": user_list})


@app.post("/post")
async def post_message(request: Request, message: str = Form(...), visible_to: List[str] = Form(...), username: str = Depends(get_current_user)):
    if not username:
        return RedirectResponse(url="/")
    new_message = Message(text=message, visible_to=visible_to, author=username)
    messages.append(new_message)
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

