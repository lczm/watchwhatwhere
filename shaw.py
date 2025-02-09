import re
from pprint import pprint
from typing import List, Optional
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from model import MovieDetail

SHAW = "https://shaw.sg"

def get_currently_showing_links() -> List[str]:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(SHAW, wait_until="load")

        # element = page.query_selector("div.col-lg-12.col-sm-12.col-xs-12")
        element = page.query_selector("#indexNowShowingMovies")

        links = set()
        # Get and print the inner text of the element.
        if element:
            inner_html = element.inner_html()
            soup = BeautifulSoup(inner_html, "html.parser")
            # Find all <a> tags with an href attribute and print each href.
            for link in soup.find_all("a", href=True):
                links.add(SHAW + link["href"])
        else:
            print("Cannot find not showing")

        browser.close()
        return links

def clean_timing(showtime):
    showtime = re.sub(r'[*+]', '', showtime).strip()  # Remove * and +
    match = re.match(r'(\d{1,2}):(\d{2})\s*(AM|PM)', showtime)
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

        title = page.locator("div.title").first.text_content()
        sypnopsis = page.locator("div.hide-for-tab.hide-for-mob").first.text_content()
        cast = page.locator("div.row.moviedetail").locator("div.col-lg-9").first.text_content()

        runtime_label = page.locator("span._label", has_text="RUNNING TIME")
        runtime = convert_to_minutes(runtime_label.locator("xpath=following-sibling::span").first.text_content().strip())

        genre_label = page.locator("span._label", has_text="GENRE")
        genre_parent = genre_label.locator("xpath=..")
        genre = genre_parent.locator("xpath=following-sibling::div").first.text_content()

        language_label = page.locator("span._label", has_text="LANGUAGE")
        language_parent = language_label.locator("xpath=..")
        language = language_parent.locator("xpath=following-sibling::div").first.text_content()

        print(title)
        print(sypnopsis)
        print(cast)
        print(runtime)
        print(genre)
        print(language)

        showtimes = {}
        movie_blocks = page.locator("div.movie_item-movie.row.block-list-showtimes").all()
        for block in movie_blocks:
            theatre_name = block.locator("div.col-lg-3 span._label").text_content().strip()
            showtime_block = block.locator("div.col-lg-8 a.cell.cell-note").all()

            showtime_list = []
            for showtime in showtime_block:
                timing = clean_timing(showtime.text_content().strip())
                href = SHAW + showtime.get_attribute("href")
                showtime_list.append((timing, href))
            showtimes[theatre_name] = showtime_list
        pprint(showtimes)

        browser.close()

def get_shaw_movies(links: List[str]) -> List[MovieDetail]:
    return None

if __name__ == "__main__":
    # links = get_currently_showing_links()
    # for link in links:
    #     get_movie_details(link)
    get_movie_details("https://shaw.sg/movie-details/1190")