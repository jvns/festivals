from pathlib import Path

from bs4 import BeautifulSoup
from dateutil import parser

from src.cache import HTTPCache
import src.showlib as showlib
from src.showlib import Show, Showtime


def scrape_theatre_de_verdure_data():
    cache = HTTPCache()

    url = "https://montreal.ca/calendrier?dc_relation.url=/lieux/theatre-de-verdure&shownResults=25"
    content = cache.fetch(url, timeout=10)
    soup = BeautifulSoup(content, "html.parser")
    events = parse_events(soup)

    return events


def parse_event(soup):
    title = soup.select_one(".list-group-item-title").text.strip()
    url = "https://montreal.ca" + soup["href"]

    # date and time
    datetime_str = soup.select_one("time").get("datetime")
    dt = parser.parse(datetime_str)

    showtime = Showtime(dt)

    return Show(
        title=title,
        showtimes=[showtime],
        link=url,
        extra={},
    )


def parse_events(soup):
    shows = []

    for s in soup.select(".list-group-item-action"):
        try:
            shows.append(parse_event(s))
        except Exception:
            print(s.prettify())
            raise
    return shows


def main():
    shows = scrape_theatre_de_verdure_data()
    shows_file = Path(__file__).parent / "shows.json"
    showlib.save(shows, shows_file, "Theatre de Verdure")


if __name__ == "__main__":
    main()
