import typer
from engine import engine
from sqlmodel import Session, SQLModel, select
from cathay import get_cathay_movies
from shaw import get_shaw_movies
from model import MovieDetail

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
            assert(len(new_movie.cinemas)) == 1
            # Check if movie already exists
            stmt = select(MovieDetail).where(MovieDetail.title == new_movie.title)
            existing_movie = session.exec(stmt).first()
            if existing_movie:
                # group cinemas together
                if new_movie.cinemas[0] not in existing_movie.cinemas:
                    existing_movie.cinemas.append(new_movie.cinemas[0])
                # update all movie showtimes to refer back to the same
                for showtime in new_movie.showtimes:
                    showtime.movie = existing_movie
                    session.add(showtime)
            else:
                # For new movies, initialize cinema as a list
                new_movie.cinemas = [new_movie.cinemas]
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