from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="sox.bot", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sox.bot", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
