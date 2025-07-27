from pathlib import Path

from bs4 import BeautifulSoup
from dateutil import parser

from src.cache import HTTPCache
import src.showlib as showlib
from src.showlib import Show, Showtime


def scrape_fireworks_data():
    cache = HTTPCache()

    # Minimal headers to avoid being blocked
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:140.0) Gecko/20100101 Firefox/140.0",
        "Referer": "https://www.sixflags.com/larondeen/events/linternational-des-feux",
        "Sec-Fetch-Dest": "document",
    }

    main_url = "https://www.sixflags.com/larondeen/linternational-des-feux/program"
    content = cache.fetch(main_url, headers=headers, timeout=10)
    soup = BeautifulSoup(content, "html.parser")
    for link in soup.find_all("a"):
        if link.get("href"):
            link.replace_with(link["href"])
    parts = soup.get_text().split("\n")
    parts = [p.strip() for p in parts]
    parts = [p for p in parts if len(p.strip()) > 0]
    idx = parts.index("Program")
    parts = parts[idx:]
    events = set()
    for i, part in enumerate(parts):
        if ", 2025" in part and "summer" not in part:
            title = parts[i - 1]
            date = part.replace(" ,", ",")
            url = get_url(parts, i)
            events.add((date, title, url))

    shows = []
    sorted_events = sorted(events, key=lambda x: parser.parse(x[0]))
    for date_str, title, url in sorted_events:
        parsed_date = parser.parse(date_str)
        show_date = parsed_date.replace(hour=22, minute=0, second=0, microsecond=0)

        showtime = Showtime(show_date, "")
        show = Show(title=title, showtimes=[showtime], link=url, extra={})
        shows.append(show)

    return shows


def get_url(parts, i):
    for p in parts[i:]:
        if "http" in p:
            return p


if __name__ == "__main__":
    shows = scrape_fireworks_data()
    shows_file = Path(__file__).parent / "shows.json"
    showlib.save(shows, shows_file, "Fireworks")
