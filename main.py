from fastapi import FastAPI

from chat.controller import router

app = FastAPI(
    title="Payment Collection Agent"
)

app.include_router(router)