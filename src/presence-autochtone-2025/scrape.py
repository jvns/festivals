from datetime import datetime
from pathlib import Path
import re
from concurrent.futures import ThreadPoolExecutor

from bs4 import BeautifulSoup
from dateutil import parser
from html_sanitizer.sanitizer import Sanitizer

from src.cache import HTTPCache
import src.showlib as showlib
from src.showlib import Show, Showtime


def get_shows():
    cache = HTTPCache()

    url = "https://presenceautochtone.ca/en/the-festival/calendar/"
    content = cache.fetch(url, timeout=10)
    soup = BeautifulSoup(content, "html.parser")

    shows = []
    container = soup.find(class_="uk-filter-container")
    for event in container.find_all(class_="uk-box-content"):
        date_wrapper = event.find(class_="uk-time")
        if not date_wrapper:
            continue
        dates = parse_dates(date_wrapper.get_text().strip())
        if not dates:
            continue

        link = event.find(class_="uk-h4")
        title = link.get_text().strip()
        url = link["href"]

        venue_wrapper = event.find(class_="uk-location")
        venue = None
        if venue_wrapper:
            venue = venue_wrapper.get_text().strip()

        showtimes = [Showtime(date, venue) for date in dates]
        show = Show(title=title, showtimes=showtimes, link=url, extra={})
        shows.append(show)

    with ThreadPoolExecutor(max_workers=8) as executor:
        shows = list(executor.map(lambda s: fetch_description(cache, s), shows))
    return shows

def parse_dates(date_text):
    results = []
    day, times = re.search(r"(August\s+\d+), (.*)",
                          date_text, flags=re.I).groups()
    times = re.split(r"\s*(?:&|and|,)\s*", times, flags=re.I)
    for time in times:
        time = re.sub(r"(de|from)", "", time, flags=re.I)
        time = re.sub(r"(à|to).*", "", time, flags=re.I) # ignore end times
        time = re.sub(r"pm pm", "pm", time) # silly typo
        results.append(parser.parse(f"{day} {time}"))

    return results

def fetch_description(cache, show):
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0"
    }
    content = cache.fetch(show.link, headers=headers, timeout=10)
    soup = BeautifulSoup(content, "html.parser")

    if (text_wrapper := soup.find(class_="uk-text")):
        show.extra["description"] = Sanitizer().sanitize(text_wrapper.decode_contents())

    if (cover_wrapper := soup.find(class_="uk-cover-container")):
        if (cover_img := cover_wrapper.find("img")):
            show.extra["image"] = cover_img["data-src"]

    return show

def main():
    shows = get_shows()
    shows_file = Path(__file__).parent / "shows.json"
    showlib.save(shows, shows_file, "Présence Autochtone")


if __name__ == "__main__":
    main()