import typer
from engine import engine
from sqlmodel import Session, SQLModel
from cathay import get_cathay_movies

app = typer.Typer()

@app.command()
def drop():
    SQLModel.metadata.drop_all(bind=engine)

@app.command()
def create():
    SQLModel.metadata.create_all(engine)

@app.command()
def scrape():
    cathay_movies = get_cathay_movies()
    with Session(engine) as session:
        session.add_all(cathay_movies)
        session.commit()
        for movie in cathay_movies:
            session.refresh(movie)

@app.command()
def drop_create_scrape():
    SQLModel.metadata.drop_all(bind=engine)
    SQLModel.metadata.create_all(engine)
    cathay_movies = get_cathay_movies()
    with Session(engine) as session:
        session.add_all(cathay_movies)
        session.commit()
        for movie in cathay_movies:
            session.refresh(movie)


if __name__ == "__main__":
    app()