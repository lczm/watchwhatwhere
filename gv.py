import re
from datetime import date,time, datetime


from pprint import pprint
from typing import List
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

def clean_gv_synopsis(synopsis:str) -> str:
    """
    We split at the first "<br />" and take only the first half of the string.
    """
    clean_synopsis = re.split(r"<br\s*/?>", synopsis, maxsplit=1)[0].strip()
    return clean_synopsis

def clean_gv_date(date_ms: int) -> date:
    return datetime.fromtimestamp(date_ms / 1000).date()

def clean_gv_time(time_str: str) -> time:
    return datetime.strptime(time_str, "%I:%M%p").time()

def get_gv_date_for_href(date_ms: int) -> str:
    date = datetime.fromtimestamp(date_ms / 1000)
    return date.strftime("%d-%m-%Y")

def playwright_for_gv():
    """
    This is the base function for playwright
    It takes in a URL and returns the page along with browser activity.
    This is so that you can close browser and playwright in the other function.
    """
    p = sync_playwright().start()
    # `headless=False` simulates a visible browser
    browser = p.chromium.launch(
        headless=True, # Set to false for testing
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



    return p, browser, page

#_________________________________________________________________________________
#
#                                  MAIN FUNCTIONS
# ________________________________________________________________________________

def get_all_gv_movies_links() -> List[MovieTitle]:
    """
    Gets a list of all GV Movies and its link.
    """
    p, browser, page = playwright_for_gv() 
    
    # === Navigate ===
    page.goto(GV_MOVIES, wait_until="load")

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
    from pprint import pprint

    p, browser, page = playwright_for_gv()

    # Prepare to capture both API responses
    with page.expect_response(lambda r: ".gv-api/filminfo" in r.url and r.request.method == "POST") as film_info_promise, \
         page.expect_response(lambda r: ".gv-api/sessionforfilm" in r.url and r.request.method == "POST") as session_info_promise:
        
        # Then we nagivate to the url
        page.goto(movie.href, wait_until="load")
        page.wait_for_timeout(6000)  # Give JS time to run
        page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        page.wait_for_timeout(4000)

    # Capture responses
    film_info_response = film_info_promise.value
    session_info_response = session_info_promise.value
    film_info_json = film_info_response.json()
    session_info_json = session_info_response.json()

    opening_date_raw = film_info_json["data"]["releaseDate"]
    opening_date = datetime.fromtimestamp(opening_date_raw / 1000)
    formatted_opening_date = opening_date.strftime("%d %b %Y")

    synopsis_raw=film_info_json["data"]["synopsis"]
    synopsis = clean_gv_synopsis(synopsis_raw)

    # === Cleanup ===
    browser.close()
    p.stop()
    showtimes = []

    film_code = session_info_json["data"]["filmCd"]

    # need to  to get the values instead of the keys.
    for location in session_info_json["data"]["locations"]:
        cinema_id = location["id"] 
        cinema_name = location["name"]
        for dates in location["dates"]:
            session_date_obj = clean_gv_date(dates["date"])
            show_date = get_gv_date_for_href(dates["date"])
            for times in dates["times"]:
                session_time_obj = clean_gv_time(times["time12"])
                session_time_24h = times["time24"]
                hall_number = times["hallNumber"]
                href = (
                    f"https://www.gv.com.sg/GVSeatSelection#/cinemaId/{cinema_id}"
                    f"/filmCode/{film_code}"
                    f"/showDate/{show_date}"
                    f"/showTime/{session_time_24h}"
                    f"/hallNumber/{hall_number}"
                )

                showtimes.append(
                       Showtime(
                            cinema=GV,
                            location=cinema_name,
                            date=session_date_obj,
                            time=session_time_obj,
                            link=href,
                        )
               ) 

    return MovieDetail(
        title=movie.title,
        synopsis=synopsis,
        cast=film_info_json["data"]["mainCast"],
        genre=film_info_json["data"]["genre"],
        language=film_info_json["data"]["language"],
        rating=film_info_json["data"]["rating"],
        runtime=film_info_json["data"]["duration"],
        opening_date=formatted_opening_date,
        showtimes=showtimes,
        cinemas=[GV],
    )


def get_gv_movies() -> List[MovieDetail]:
    movies = get_all_gv_movies_links()
    movie_details = [get_gv_movie_details(movie) for movie in movies]

    return movie_details

if __name__ == "__main__":
    movies = get_all_gv_movies_links()
    movie_details_list = [get_gv_movie_details(movie) for movie in movies]
    pprint(movie_details_list)
