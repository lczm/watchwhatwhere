import asyncio
import uvicorn
from datetime import datetime
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import Depends, FastAPI
from sqlmodel import Session, select
from sqlalchemy import and_
from model import MovieDetail, Showtime
from fastapi_utilities import repeat_every
from commands import drop_create_scrape
from engine import engine

# Gets a database session
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# Things that need to run on start up
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(hourly())
    yield

app = FastAPI(lifespan=lifespan)

# Run every hour
@repeat_every(seconds=60*60*6, wait_first=True)
def hourly():
    drop_create_scrape()

@app.get("/watchwhatwhere/")
async def movies(session: SessionDep):
    return session.exec(select(MovieDetail)).all()

@app.get("/watchwhatwhere/movies/{movie_id}")
async def movie(movie_id: int, session: SessionDep):
    return session.exec(select(MovieDetail).where(MovieDetail.id == movie_id)).first()

@app.get("/watchwhatwhere/showtimes/{movie_id}")
async def showtimes(movie_id: int, session: SessionDep):
    return session.exec(select(Showtime).where(and_(Showtime.movie_id == movie_id, Showtime.date >= datetime.now()))).all()

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)