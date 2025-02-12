import requests
from bs4 import BeautifulSoup
from typing import List
from pprint import pprint
from datetime import datetime
from model import Showtime, MovieTitle, MovieDetail
from utils import clean_title_remove_brackets

CATHAY_HOME = "https://www.cathaycineplexes.com.sg/"
CATHAY = "Cathay"


def clean_title(title: str) -> str:
    title = title.strip()
    # If title ends with asterisk, remove it first
    if title.endswith("*"):
        title = title[:-1].strip()
    # Then clean the PG ratings out, this can be gotten later on
    title = " ".join(title.split()[:-1])
    # Remove all brackets that exist as well
    return clean_title_remove_brackets(title)


def scrape_cathay_movies() -> List[MovieTitle]:
    """
    Scrapes currently showing movies from Cathay Cineplexes website.
    Returns a list of CathayMovie objects containing movie titles and their links.
    """
    try:
        # Fetch the webpage content
        response = requests.get(CATHAY_HOME)
        response.raise_for_status()

        # Parse the HTML
        content = response.text
        soup = BeautifulSoup(content, "html.parser")

        # Find the "Now Showing" tab content
        now_showing_div = soup.find("div", {"id": "tab1"})

        movies = []
        if now_showing_div:
            # Find all movie containers
            movie_containers = now_showing_div.find_all("div", class_="movie-container")

            for container in movie_containers:
                # Find the anchor tag containing the movie link
                movie_link = container.find("a")
                if movie_link:
                    href = movie_link.get("href", "")
                    # Title is in a nested div with class 'text-[#43b8ff]'
                    title_div = container.find("div", class_="text-[#43b8ff]")
                    if title_div:
                        # Clean up the title by removing rating and asterisk
                        title = clean_title(title_div.text)
                        movies.append(MovieTitle(title=title, href=href))

        return movies

    except Exception as e:
        print(f"Error scraping Cathay movies: {e}")
        return []


def scrape_cathay_movie_detail(movie: MovieTitle) -> MovieDetail:
    """
    Extract movie details by making a request to the movie's detail page URL.
    Returns a CathayMovieDetails object containing parsed movie information.
    """
    try:
        # Make web request to movie detail page
        response = requests.get(movie.href)
        response.raise_for_status()

        # Parse the HTML content
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract movie name from the blue title text
        movie_name_div = soup.find("div", class_="text-[#43b8ff]")
        movie_name = clean_title(movie_name_div.text) if movie_name_div else ""

        # Extract synopsis from the text under SYNOPSIS
        synopsis_div = cast_div = genre_div = language_div = rating_div = (
            runtime_div
        ) = opening_div = None
        sections = soup.find_all("div", class_="text-[14px] text-[#43b8ff] font-bold")
        for section in sections:
            if section.text == "SYNOPSIS":
                synopsis_div = section.parent.find(
                    "div", class_="text-[14px] leading-[17px] pr-[20px] text-white"
                )
            elif section.text == "CAST":
                cast_div = section.parent.find(
                    "div", class_="text-[14px] leading-[17px] text-white"
                )
            elif section.text == "GENRE":
                genre_div = section.parent.find(
                    "div",
                    class_="text-white text-[14px] lg:leading-[14px] lg:my-0 my-auto",
                )
            elif section.text == "LANGUAGE":
                language_div = section.parent.find(
                    "div",
                    class_="text-white text-[14px] leading-[14px] lg:my-0 my-auto",
                )
            elif section.text == "RATING":
                rating_div = section.parent.find(
                    "div",
                    class_="movie-rating text-white text-[14px] leading-[14px] lg:my-0 my-auto whitespace-nowrap",
                )
            elif section.text == "RUNTIME":
                runtime_div = section.parent.find(
                    "div",
                    class_="text-white text-[14px] leading-[14px] lg:my-0 my-auto",
                )
            elif section.text == "OPENING":
                opening_div = section.parent.find(
                    "div",
                    class_="ext-white text-[15px] leading-[14px] whitespace-nowrap lg:my-0 my-auto",
                )

        synopsis = " ".join(synopsis_div.text.split()).strip() if synopsis_div else ""
        cast = " ".join(cast_div.text.split()).strip() if cast_div else ""
        genre = " ".join(genre_div.text.split()).strip() if genre_div else ""
        language = " ".join(language_div.text.split()).strip() if language_div else ""
        rating = " ".join(rating_div.text.split()).strip() if rating_div else ""
        runtime = " ".join(runtime_div.text.split()).strip() if runtime_div else ""
        opening_div = " ".join(opening_div.text.split()).strip() if opening_div else ""

        # Extract showtimes data
        showtimes = []
        showtime_data = soup.find_all("div", class_="show-time-data")

        for data in showtime_data:
            location = data.get("cinema_name", "")
            # Parse date string into date object
            date_str = data.get("date_full", "").split("T")[0]
            show_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Parse time string into time object
            time_str = data.get("show_time", "")
            show_time = datetime.strptime(time_str, "%H:%M").time()

            link = data.get("link", "")

            showtimes.append(
                Showtime(
                    cinema=CATHAY,
                    location=location,
                    date=show_date,
                    time=show_time,
                    link=link,
                )
            )

        return MovieDetail(
            title=movie_name,
            synopsis=synopsis,
            cast=cast,
            genre=genre,
            language=language,
            rating=rating,
            runtime=runtime,
            opening_date=opening_div,
            showtimes=showtimes,
            cinemas=[CATHAY],
        )

    except Exception as e:
        print(f"Error parsing movie details from {movie.href}: {e}")
        return None


def get_cathay_movies() -> List[MovieDetail]:
    movies = scrape_cathay_movies()
    movie_details = [scrape_cathay_movie_detail(movie) for movie in movies]
    return movie_details


if __name__ == "__main__":
    movies = scrape_cathay_movies()
    movie_details = [scrape_cathay_movie_detail(movie) for movie in movies]
    pprint(movie_details)
