from pathlib import Path

from bs4 import BeautifulSoup
from dateutil import parser

from src.cache import HTTPCache
import src.showlib as showlib
from src.showlib import Show, Showtime


def scrape_shakespeare_data():
    cache = HTTPCache()
    url = "https://www.repercussiontheatre.com/summer-tour-2025/"
    content = cache.fetch(url, timeout=10)
    soup = BeautifulSoup(content, "html.parser")
    showtimes = list(parse_showtimes(soup))

    return [
        Show(
            title="The Importance of Being Earnest",
            showtimes=showtimes,
            link=url,
            extra={
                "company": "Repercussion Theatre",
            },
        )
    ]


def parse_showtime(soup):
    # Skip divs that don't have tour date info (h3 elements)
    h3 = soup.find("h3")
    if not h3:
        return None

    # Extract venue info from h6 elements
    h6_elements = soup.find_all("h6")
    venue_parts = []
    for h6 in h6_elements:
        h6_text = h6.get_text().strip()
        venue_parts.append(h6_text.rstrip(",").strip())

    # Parse the date string (e.g., "July 24, 7pm")
    h3_text = h3.get_text().strip()
    date_str = f"{h3_text}, 2025"
    dt = parser.parse(date_str)

    park = venue_parts[0]
    city = venue_parts[1] if len(venue_parts) >= 2 else ""
    venue = " / ".join(venue_parts)

    return Showtime(dt, venue, extra={"city": city, "park": park})


def parse_showtimes(soup):
    text_divs = soup.select("div.et_pb_text_inner")[2:]
    for s in text_divs:
        try:
            showtime = parse_showtime(s)
            if showtime is not None:
                yield showtime
        except Exception:
            print(s.prettify())
            raise


def main():
    shows = scrape_shakespeare_data()
    shows_file = Path(__file__).parent / "shows.json"
    showlib.save(shows, shows_file, "Shakespeare")


if __name__ == "__main__":
    main()
