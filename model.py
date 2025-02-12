from dataclasses import dataclass
from datetime import date, time
from typing import List, Optional

from sqlmodel import JSON, Field, Relationship, SQLModel


@dataclass
class MovieTitle:
    title: str
    href: str


class MovieDetail(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    synopsis: str
    cast: str
    genre: str
    language: str
    rating: Optional[str] = Field(default=None)
    runtime: str
    opening_date: Optional[str] = Field(default=None)
    cinemas: List[str] = Field(sa_type=JSON)

    # Relationship to "Showtime"
    # Note the string reference to "Showtime" if you define this class first
    showtimes: List["Showtime"] = Relationship(back_populates="movie")


class Showtime(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    cinema: str
    location: str
    date: date
    time: time
    link: str

    # Foreign Key referencing MovieDetail
    movie_id: Optional[int] = Field(default=None, foreign_key="moviedetail.id")

    # Relationship back to MovieDetail
    movie: Optional[MovieDetail] = Relationship(back_populates="showtimes")
