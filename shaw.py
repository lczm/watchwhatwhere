import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pprint import pprint
from typing import List, Optional

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from tqdm import tqdm

from model import MovieDetail, Showtime
from utils import clean_title_remove_brackets

SHAW_HOME = "https://shaw.sg"
SHAW = "Shaw"


def get_currently_showing_links() -> List[str]:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(SHAW_HOME, wait_until="load")

        # element = page.query_selector("div.col-lg-12.col-sm-12.col-xs-12")
        element = page.query_selector("#indexNowShowingMovies")

        links = set()
        # Get and print the inner text of the element.
        if element:
            inner_html = element.inner_html()
            soup = BeautifulSoup(inner_html, "html.parser")
            # Find all <a> tags with an href attribute and print each href.
            for link in soup.find_all("a", href=True):
                links.add(SHAW_HOME + link["href"])
        else:
            print("Cannot find not showing")

        browser.close()
        return links


def clean_timing(showtime):
    showtime = re.sub(r"[*+]", "", showtime).strip()  # Remove * and +
    match = re.match(r"(\d{1,2}):(\d{2})\s*(AM|PM)", showtime)
    if match:
        hour, minutes, period = match.groups()
        hour = hour.zfill(2)
        return f"{hour}:{minutes} {period}"
    return showtime


def convert_to_minutes(time_str) -> Optional[str]:
    match = re.match(r"(?:(\d+) hr)?\s*(?:(\d+) mins?)?", time_str)

    if match:
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        return str(hours * 60 + minutes) + " mins"

    return None  # Return None if format is invalid


def get_movie_details(link: str) -> MovieDetail:
    print(link)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(link, wait_until="load")

        title = clean_title_remove_brackets(
            page.locator("div.title").first.text_content()
        )
        sypnopsis = page.locator("div.hide-for-tab.hide-for-mob").first.text_content()
        cast = (
            page.locator("div.row.moviedetail")
            .locator("div.col-lg-9")
            .first.text_content()
        )

        runtime_label = page.locator("span._label", has_text="RUNNING TIME")
        runtime = convert_to_minutes(
            runtime_label.locator("xpath=following-sibling::span")
            .first.text_content()
            .strip()
        )

        genre_label = page.locator("span._label", has_text="GENRE")
        genre_parent = genre_label.locator("xpath=..")
        genre = genre_parent.locator(
            "xpath=following-sibling::div"
        ).first.text_content()

        language_label = page.locator("span._label", has_text="LANGUAGE")
        language_parent = language_label.locator("xpath=..")
        language = language_parent.locator(
            "xpath=following-sibling::div"
        ).first.text_content()

        showtimes = []
        owl_stage = page.locator("div.owl-stage")
        date_elements = owl_stage.locator("span.date").all()
        for date_element in date_elements:
            date_text = date_element.text_content().strip()
            date_object = datetime.strptime(date_text, "%d %b %Y").date()
            date_element.click()
            time.sleep(2)

            movie_blocks = page.locator(
                "div.movie_item-movie.row.block-list-showtimes"
            ).all()
            for block in movie_blocks:
                theatre_name = (
                    block.locator("div.col-lg-3 span._label").text_content().strip()
                )
                showtime_block = block.locator("div.col-lg-8 a.cell.cell-note").all()

                for showtime in showtime_block:
                    timing = clean_timing(showtime.text_content().strip())
                    time_object = datetime.strptime(timing, "%I:%M %p").time()
                    href = SHAW_HOME + showtime.get_attribute("href")
                    showtimes.append(
                        Showtime(
                            cinema=SHAW,
                            location=theatre_name,
                            date=date_object,
                            time=time_object,
                            link=href,
                        )
                    )
        browser.close()
        return MovieDetail(
            title=title,
            synopsis=sypnopsis,
            cast=cast,
            genre=genre,
            language=language,
            rating=None,
            runtime=runtime,
            opening_date=None,
            showtimes=showtimes,
            cinemas=[SHAW],
        )


def get_shaw_movies(workers=1) -> List[MovieDetail]:
    movies = get_currently_showing_links()
    movie_details = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(get_movie_details, movie) for movie in movies]
        for future in tqdm(
            as_completed(futures), total=len(futures), desc="Processing movies"
        ):
            movie_details.append(future.result())

    return movie_details


if __name__ == "__main__":
    pprint(get_shaw_movies())
