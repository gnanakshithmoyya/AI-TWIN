# app/main.py

from fastapi import FastAPI
from app.chat import router as chat_router
from app.rag.loader import load_docs

app = FastAPI()

@app.on_event("startup")
def startup():
    load_docs()

app.include_router(chat_router)