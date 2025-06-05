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

#_________________________________________________________________________________
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





def get_gv_movie_details(url_link: str) -> str:
    from pprint import pprint

    requests_captured = {}

    def handle_request(request):
        url = request.url
        if request.method == "POST":
            print(f"🛰️ {request.method} {url}")
            if ".gv-api/filminfo" in url:
                print(f"✅ Captured filminfo request: {url}")
                print("Payload:", request.post_data)
                requests_captured["film_info"] = (url, request.post_data)
            elif ".gv-api/sessionforfilm" in url:
                print(f"✅ Captured sessionforfilm request: {url}")
                print("Payload:", request.post_data)
                requests_captured["session_info"] = (url, request.post_data)

    # 1. Start browser and visit the homepage first
    p, browser, page = playwright_for_gv("https://www.gv.com.sg/")
    page.on("request", handle_request)
    page.wait_for_timeout(4000)  # Wait for homepage JS/cookies

    # 2. Now navigate to movie detail page
    page.goto(url_link, wait_until="domcontentloaded")
    page.wait_for_timeout(14000)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
    page.wait_for_timeout(5000)  # Let any lazy-loaders fire

    print("Requests captured:", requests_captured.keys())
    film_info = requests_captured.get("film_info")
    session_info = requests_captured.get("session_info")

    browser.close()
    p.stop()

    if not film_info or not session_info:
        raise Exception("❌ One or both required API requests were not captured.")

    print("FILM INFO REQUEST URL:", film_info[0])
    print("FILM INFO PAYLOAD:", film_info[1])
    print("SESSION REQUEST URL:", session_info[0])
    print("SESSION PAYLOAD:", session_info[1])
    return "finished"


if __name__ == "__main__":
    movie_details = get_gv_movie_details("https://www.gv.com.sg/GVMovieDetails?movie=1276#/movie/1276")
    pprint(movie_details)
