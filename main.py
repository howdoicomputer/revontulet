from fastapi import FastAPI
from .routers import sats
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)


app.include_router(sats.router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Welcome to the API; all routes are on /api"}
