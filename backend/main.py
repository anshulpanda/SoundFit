from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import spotify, outfits

app = FastAPI(title="SoundFit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(spotify.router, prefix="/auth", tags=["auth"])
app.include_router(outfits.router, prefix="/outfits", tags=["outfits"])


@app.get("/health")
async def health():
    return {"status": "ok"}
