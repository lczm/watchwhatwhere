import uvicorn
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi import Depends, FastAPI
from sqlmodel import Session, create_engine, select, SQLModel
from model import MovieDetail, Showtime

DATABASE_URL = "sqlite:///watchwhatwhere.db"
engine = create_engine(DATABASE_URL, echo=True)

# Gets a database session
def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

# Load DB schema and load all data into it
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Commented out to make things fast
    # SQLModel.metadata.drop_all(bind=engine)
    # SQLModel.metadata.create_all(engine)
    # cathay_movies = get_cathay_movies()
    # with Session(engine) as session:
    #     session.add_all(cathay_movies)
    #     session.commit()
    #     for movie in cathay_movies:
    #         session.refresh(movie)
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/watchwhatwhere/")
async def movies(session: SessionDep):
    return session.exec(select(MovieDetail)).all()

@app.get("/watchwhatwhere/movies/{movie_id}")
async def movie(movie_id: int, session: SessionDep):
    return session.exec(select(MovieDetail).where(MovieDetail.id == movie_id)).first()

@app.get("/watchwhatwhere/showtimes/{movie_id}")
async def showtimes(movie_id: int, session: SessionDep):
    return session.exec(select(Showtime).where(Showtime.movie_id == movie_id)).all()

if __name__ == '__main__':
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)