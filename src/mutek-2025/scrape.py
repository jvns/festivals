import json
from pathlib import Path

from bs4 import BeautifulSoup
from dateutil import parser

from src.cache import HTTPCache
import src.showlib as showlib
from src.showlib import Show, Showtime


def scrape_mutek_data():
    cache = HTTPCache()

    all_events = []

    base_url = "https://montreal.mutek.org/ajax/programs/920"
    dates = ["19.08", "20.08", "21.08", "22.08", "23.08", "24.08"]

    for date in dates:
        url = f"{base_url}?date={date}"
        content = cache.fetch(url, timeout=10)
        data = json.loads(content)
        soup = BeautifulSoup(data["html"], "html.parser")
        events = parse_events_for_date(soup, date)
        all_events.extend(events)

    return all_events


def parse_event(soup, date_str):
    title = soup.select_one(".single-show__title span").text.strip()

    # Extract artists
    artists = []
    for artist in soup.select(".single-show__artist span"):
        artist_name = artist.get_text().strip()
        sup_elem = artist.find("sup")
        if sup_elem:
            country_code = sup_elem.get_text()
            artist_name = artist_name.replace(country_code, f" ({country_code})")
        artists.append(artist_name)
    company = ", ".join(artists)

    # Extract location/venue
    venue = soup.select_one(".single-show__location").text.strip()

    # Extract URL
    url = soup.select_one(".single-show__title")["href"]

    free = soup.select_one(".single-show__ctas .btn-label").text.strip()
    if free == "Free":
        ticket_status = "free"
    else:
        ticket_status = "ticketed"

    # Extract date and time
    date_info = soup.select(".single-show__date p")
    assert len(date_info) >= 2
    time_text = date_info[1].text.strip()  # "6:30 pm_11:00 pm"
    start_time = time_text.split("_")[0].strip()  # "6:30 pm"
    datetime_str = f"2025-08-{date_str.split('.')[0]} {start_time}"
    dt = parser.parse(datetime_str)

    showtime = Showtime(dt, venue)

    return Show(
        title=title,
        showtimes=[showtime],
        link=url,
        extra={
            "artists": company,
            "ticket_status": ticket_status,
        },
    )


def parse_events_for_date(soup, date_str):
    shows = []
    for s in soup.select(".single-show"):
        try:
            shows.append(parse_event(s, date_str))
        except Exception:
            print(s.prettify())
            raise
    return shows


def main():
    shows = scrape_mutek_data()
    shows_file = Path(__file__).parent / "shows.json"
    showlib.save(shows, shows_file, "MUTEK")


if __name__ == "__main__":
    main()
