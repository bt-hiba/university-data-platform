from fastapi import FastAPI
from api.config import API_TITLE, API_VERSION, API_DESCRIPTION
from api.routes import router

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(router)

@app.get("/", tags=["Health"])
def health_check():
    return {"status": "online", "message": "University Data Platform Search API is running."}