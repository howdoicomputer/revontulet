from fastapi import FastAPI
from .routers import sats
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI()
Instrumentator().instrument(app).expose(app)

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(sats.router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "Welcome to the API; all routes are on /api"}
