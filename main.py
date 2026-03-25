from fastapi import FastAPI
from api.router import router

app = FastAPI(
    title="itamityt API"
)

app.include_router(router)