from fastapi import FastAPI
import uvicorn
from tortoise import Tortoise

from config import database_url, debug_mode, host, port
from src.router.user import router as user_router

app = FastAPI()
app.include_router(user_router)

@app.route("/health")
async def health_check():
    return {"status": "ok"}

@app.on_event("startup")
async def init_orm() -> None:
    await Tortoise.init(
        db_url=database_url,
        modules={"models": ["src.model.user", "src.model.post"]},
    )
    await Tortoise.generate_schemas()

@app.on_event("shutdown")
async def close_orm() -> None:
    await Tortoise.close_connections()

if __name__ == "__main__":
    uvicorn.run("main:app", host=host, port=port, reload=debug_mode)
