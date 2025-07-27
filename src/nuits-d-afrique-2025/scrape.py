from pathlib import Path

from bs4 import BeautifulSoup
from dateutil import parser

from src.cache import HTTPCache
import src.showlib as showlib
from src.showlib import Show, Showtime


def scrape_nuits_afrique_data():
    cache = HTTPCache()
    url = "https://www.festivalnuitsdafrique.com/en/programmation-festival-nuits-dafrique-2025-gratuit/?category=664&concert=yes"
    content = cache.fetch(url, timeout=10)
    soup = BeautifulSoup(content, "html.parser")

    shows = []

    event_cards = soup.select(".event-card")

    for card in event_cards:
        try:
            shows.append(parse_event_card(card, cache))
        except Exception:
            print(card.prettify())
            raise

    return shows


def parse_event_card(card, cache):
    """Parse a single event card to extract show information"""
    artist = card.find(class_="event-card-title").text.strip()

    # Extract date and time
    overlay = card.find(class_="event-card-overlay")
    date_spans = overlay.find_all("span")
    assert len(date_spans) >= 3

    day_number = date_spans[1].get_text().strip()
    month_name = date_spans[2].get_text().strip()

    time_elem = overlay.find(class_="event-time")
    time_text = time_elem.get_text().strip()

    date_string = f"{day_number} {month_name} 2025 {time_text}"
    dt = parser.parse(date_string)

    link = card.get("href")

    image = ""
    detail_content = cache.fetch(link, timeout=10)
    detail_soup = BeautifulSoup(detail_content, "html.parser")

    # Extract description
    desc_elem = detail_soup.select_one(".text-container")
    if desc_elem:
        description = desc_elem.get_text().strip()
    else:
        desc_elem = detail_soup.select_one(".description")
        if desc_elem:
            description = desc_elem.get_text().strip()

    # Extract image
    img_cont = detail_soup.select_one(".img-cont")
    if img_cont:
        img_elem = img_cont.find("img")
        image = img_elem.get("src", "")
        if image and not image.startswith("http"):
            image = "https://www.festivalnuitsdafrique.com" + image

    showtime = Showtime(dt)
    return Show(
        title=artist,
        showtimes=[showtime],
        link=link,
        extra={
            "image": image,
            "description": description,
        },
    )


def extract_venue(card):
    """Extract venue information from the event card"""
    text = card.get_text()

    if "scène td" in text.lower():
        return "Scène TD"
    elif "scène loto-québec" in text.lower():
        return "Scène Loto-Québec"
    elif "loto-québec" in text.lower():
        return "Scène Loto-Québec"

    return "Festival International Nuits d'Afrique"


def main():
    shows = scrape_nuits_afrique_data()
    shows_file = Path(__file__).parent / "shows.json"
    showlib.save(shows, shows_file, "Nuits D'Afrique")


if __name__ == "__main__":
    main()
