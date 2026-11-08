from fastapi import FastAPI, HTTPException, Request, Depends
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ValidationError, Field
from contextlib import asynccontextmanager
from .db.database import TaskRepository
from dotenv import load_dotenv
import uvicorn
import asyncpg
import os

load_dotenv()

db_pool = None
repo = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global db_pool, repo
    db_pool = await asyncpg.create_pool(
        dsn = os.getenv('DB_SETTING'),
        min_size=2,
        max_size=10,
        command_timeout=30,
        max_inactive_connection_lifetime=300
    )
    repo = TaskRepository(db_pool)
    yield
    await db_pool.close()
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
templates = Jinja2Templates(directory='src/app/templates')
class CreateTask(BaseModel):
    title: str = Field(min_length=6, max_length=60)
    description: str = Field(min_length=10, max_length=400)
    reward: int
@app.get('/', response_class=HTMLResponse)
async def main_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name='index.html'
    )