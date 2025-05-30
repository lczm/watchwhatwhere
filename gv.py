from os import wait
import re
import time

from pprint import pprint
from typing import List, Optional

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from tqdm import tqdm

from model import MovieDetail, Showtime
from utils import clean_title_remove_brackets

GV_HOME = "https://www.gv.com.sg/GVMovies"

def get_gv_movies() -> List[str]:
    with sync_playwright() as p:
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
        page.goto(GV_HOME, wait_until="load")

        # Get page content
        element = page.query_selector("#nowMovieThumb")

        links = set()


        if element:
            inner_html = element.inner_html()
            soup = BeautifulSoup(inner_html, "html.parser")
            for link in soup.find_all("a", href=True):
                links.add(GV_HOME + link["href"])
        else:
            print("Cannot find not showing")

        browser.close()
        return list(links)


if __name__ == "__main__":
    pprint(get_gv_movies())
