from typing import List
from dataclasses import dataclass
from datetime import date, time
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine

@dataclass
class Showtime:
    cinema: str
    date: date
    time: time 
    link: str

@dataclass
class MovieTitle:
    title: str
    href: str

@dataclass
class MovieDetail:
    title: str
    synopsis: str
    cast: str 
    genre: str
    language: str
    rating: str
    runtime: str
    opening_date: str
    showtimes: List[Showtime]