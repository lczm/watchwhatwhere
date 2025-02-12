import typer
from engine import engine
from sqlmodel import Session, SQLModel, select
from cathay import get_cathay_movies
from shaw import get_shaw_movies
from model import MovieDetail
from sqlalchemy import func, update

app = typer.Typer()


@app.command()
def drop():
    SQLModel.metadata.drop_all(bind=engine)


@app.command()
def create():
    SQLModel.metadata.create_all(engine)


def insert_movies(movies):
    with Session(engine) as session:
        for new_movie in movies:
            assert len(new_movie.cinemas) == 1
            # Check if movie already exists
            stmt = select(MovieDetail).where(
                # Take purely upper case
                func.upper(MovieDetail.title) == new_movie.title.upper()
            )
            existing_movie = session.exec(stmt).first()
            if existing_movie:
                if new_movie.cinemas[0] not in existing_movie.cinemas:
                    updated_cinemas = existing_movie.cinemas + [new_movie.cinemas[0]]
                    # Update the row explicitly
                    update_stmt = (
                        update(MovieDetail)
                        .where(MovieDetail.id == existing_movie.id)
                        .values(cinemas=updated_cinemas)
                    )
                    session.exec(update_stmt)
                # update all showtimes back to the same distinct entry
                for showtime in new_movie.showtimes:
                    showtime.movie = existing_movie
                    session.add(showtime)
            else:
                session.add(new_movie)
        session.commit()


@app.command()
def scrape_cathay():
    cathay_movies = get_cathay_movies()
    insert_movies(cathay_movies)


@app.command()
def scrape_shaw():
    shaw_movies = get_shaw_movies()
    insert_movies(shaw_movies)


@app.command()
def drop_create_scrape():
    # Get cathay and shaw movies
    cathay_movies = get_cathay_movies()
    shaw_movies = get_shaw_movies()

    # Drop and insert them them only after fetching them
    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(engine)
    insert_movies(cathay_movies)
    insert_movies(shaw_movies)


if __name__ == "__main__":
    app()
