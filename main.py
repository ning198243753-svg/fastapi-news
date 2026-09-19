from fastapi import FastAPI
from routers import ai, news,users,favorite,history
from fastapi.middleware.cors import CORSMiddleware
from utils.exception_register import exception_handler_register


app=FastAPI()

exception_handler_register(app)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],allow_credentials=True)

app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)
app.include_router(history.router)
app.include_router(ai.router)

