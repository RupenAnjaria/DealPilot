from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.search import router as search_router

app = FastAPI(title="DealPilot API")

# Local-only demo: allow the Vite dev server to call this API without auth.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}
