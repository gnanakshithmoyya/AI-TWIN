# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.chat import router as chat_router
from app.rag.loader import load_docs
from app.auth.router import router as auth_router
from app.chat_store.router import router as chat_store_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    load_docs()

app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(chat_store_router)
