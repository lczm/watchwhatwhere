from os import wait
import re
from datetime import date,time, datetime

from pprint import pprint
from typing import List, Optional

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

from model import MovieDetail, Showtime, MovieTitle

GV_HOME = "https://www.gv.com.sg/"
GV_MOVIES = "https://www.gv.com.sg/GVMovies"
GV = "GV"


# ________________________________________________________________________________
#
#                                 SUPPORTING FUNCTIONS
# ________________________________________________________________________________
def clean_gv_title (title:str) -> str:
    """
    GV titles usually come in the form of something like this "Disney’s Lilo & Stitch +^*"
    This function is to remove the characters added at the back
    """
    title = re.sub(r"[+^*]+$", "", title).strip()
    return title

def playwright_for_gv(url:str):
    """
    This is the base function for playwright
    It takes in a URL and returns the page along with browser activity.
    This is so that you can close browser and playwright in the other function.
    """
    p = sync_playwright().start()
    # `headless=False` simulates a visible browser
    browser = p.chromium.launch(
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process"
        ]
    )

    # Make the "user" appear more legitimate
    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1280, "height": 720},
        locale="en-US",
        timezone_id="Asia/Singapore",
        java_script_enabled=True,
        bypass_csp=True
    )

    page = context.new_page()

    # === Stealth scripts ===
    page.add_init_script("""Object.defineProperty(navigator, 'webdriver', {get: () => undefined})""")
    page.add_init_script("""Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})""")
    page.add_init_script("""Object.defineProperty(navigator, 'platform', {get: () => 'Win32'})""")
    page.add_init_script("""Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})""")
    page.add_init_script("""
        navigator.mediaDevices = {
            getUserMedia: () => Promise.resolve({}),
            enumerateDevices: () => Promise.resolve([{ kind: "videoinput" }])
        };
    """)

    # === Navigate ===
    page.goto(url, wait_until="load")

    return p, browser, page
# ________________________________________________________________________________
#
#                                  MAIN FUNCTIONS
# ________________________________________________________________________________

def get_gv_movies() -> List[MovieTitle]:
    """
    Gets a list of all GV Movies and its link.
    """
    p, browser, page = playwright_for_gv(GV_MOVIES) 

    # Get page content
    elements = page.query_selector_all("#nowMovieThumb")

    links = set()
    movies : List[MovieTitle] = []

    for element in elements:
        inner_html = element.inner_html()
        soup = BeautifulSoup(inner_html, "html.parser")
    
        all_links = soup.find_all("a", href=True)
        if all_links:
            # find the first <a> tag only, because it gives us the correct link
            first_link = all_links[0]["href"]
            link = GV_HOME + first_link
            links.add(link)

            movie_title = soup.find("h5")
            if movie_title:
                stripped_title = clean_gv_title(movie_title.text)
                movies.append(MovieTitle(title=stripped_title, href=link))

    if not links:
        print("No movie links found")

    browser.close()
    p.stop()
    return movies

def get_gv_movie_details(movie: MovieTitle) -> MovieDetail:
    """
    Extract movie detail by making a request to the movie's detail page URL.
    """
    showtimes : List[Showtime] = []
    synopsis_div = cast_div = genre_div = language_div = (
        runtime_div
    ) = opening_div = None

    p, browser, page = playwright_for_gv(movie.href)
    contents = page.content()
    soup = BeautifulSoup(contents, "html.parser")

    sections = soup.find("div", class_="col-md-8 col-sm-8 col-xs-12 col-pg-rt-zero")

    if sections:
        cast_div = soup.find(attrs={"ng-bind-html": "filminfo.mainCast"})
        genre_div = soup.find(attrs={"ng-bind-html": "filminfo.genre"})
        opening_div = soup.find(attrs={"ng-bind-html": "filminfo.formattedReleaseDate"})
        runtime_div = soup.find("div", class_="col-md-8 col-sm-7 col-xs-7 col-pg-zero ng-binding")
        language_div = soup.find(attrs={"ng-bind-html": "filminfo.languageSubtitle"})
        synopsis_div = soup.find(attrs={"ng-bind-html": "filminfo.synopsis"})

    synopsis = " ".join(synopsis_div.text.split()).strip() if synopsis_div else ""
    cast = " ".join(cast_div.text.split()).strip() if cast_div else ""
    genre = " ".join(genre_div.text.split()).strip() if genre_div else ""
    language = " ".join(language_div.text.split()).strip() if language_div else ""
    runtime = " ".join(runtime_div.text.split()).strip() if runtime_div else ""
    opening = " ".join(opening_div.text.split()).strip() if opening_div else ""

    locations_div = page.locator("div.cinemas-body.clearfix")
    list_of_locations = locations_div.locator("li a.ng-binding").all()

    for location in list_of_locations:
        location.click()
        page.wait_for_selector("div.time-body")

        all_date_and_time = page.locator("div.time-body ul.list-unstyled li.ng-scope").all() 

        for element in all_date_and_time:
            date_span = element.locator("span.date.ng-binding")
            if not date_span:
                continue
            date_str = date_span.inner_text().strip()  
            date = datetime.strptime(date_str, "%d-%m-%Y").date()
            all_times = element.locator("li.ng-scope button").all()

            for time_element in all_times:
                raw_time = time_element.inner_text().strip()  # e.g., "2:30 PM"
                time = datetime.strptime(raw_time, "%I:%M %p").time()
                showtimes.append(
                    Showtime(
                            cinema = GV,
                            location = "",
                            date = date, 
                            time = time,
                            link = movie.href,
                            )
                    )

    browser.close()
    p.stop()

    return MovieDetail(
        title=movie.title,
        synopsis=synopsis,
        cast=cast,
        genre=genre,
        language=language,
        rating=None,
        runtime=runtime,
        opening_date=opening,
        showtimes=showtimes,
        cinemas=[GV],
    )

if __name__ == "__main__":
    movies = get_gv_movies()
    movie_details = get_gv_movie_details(movies[0])
    pprint(movie_details)
