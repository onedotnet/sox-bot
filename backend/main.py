from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.router import api_router

app = FastAPI(title="sox.bot", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sox.bot", "http://localhost:3000", "http://localhost:3010", "http://192.168.3.102:3010", "http://192.168.3.102:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
