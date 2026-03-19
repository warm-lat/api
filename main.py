from fastapi import FastAPI
from routes import *

api = FastAPI(
    title="Warm API",
    version="0.0.1",
    redoc_url=None,
    openapi_url="/openapi.json",
    docs_url="/"
)

api.include_router(social)