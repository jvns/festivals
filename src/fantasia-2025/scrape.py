"""
Fetch Fantasia program data directly from the API and convert to fringe format
"""

import json
from datetime import datetime, timedelta
from pathlib import Path

from bs4 import BeautifulSoup
from dateutil import parser

from src.cache import HTTPCache
import src.showlib as showlib
from src.showlib import Show, Showtime


def get_shows():
    cache = HTTPCache()

    start_dt = datetime(2025, 7, 16)
    end_dt = datetime(2025, 8, 3)

    shows = []

    current_date = start_dt
    while current_date <= end_dt:
        timestamp = int(current_date.timestamp()) + (
            5 * 3600
        )  # Montreal timezone offset
        url = f"https://fantasiafestival.com/en/api/horaire/{timestamp}/program"

        headers = {
            "Referer": f"https://fantasiafestival.com/en/schedule?date={current_date.strftime('%Y-%m-%d')}"
        }

        content = cache.fetch(url, headers=headers, timeout=10)
        data = json.loads(content)

        if data:
            for x in data["data"]:
                try:
                    shows.append(process_event(x))
                except Exception:
                    print(x)
                    raise

        current_date += timedelta(days=1)

    return shows



def process_event(event):
    soup = BeautifulSoup(event["html"], "html.parser")
    director = ""
    director_div = soup.select_one(".block--media__content__visible  .small")
    if director_div is not None:
        director = director_div.text
    url = soup.find("a")["href"]
    country = soup.select_one(".block--media__specs span").text
    description = soup.select_one(".block--media__content__hidden").text.strip()

    duration = soup.select(".block--media__specs span")[1].text
    assert 'mins' in duration
    duration = int(duration.split()[0])

    # Extract image
    image_url = ""
    img_tag = soup.find("img")
    if img_tag:
        srcset = img_tag.get("data-srcset", "")
        if srcset:
            image_url = srcset
        else:
            image_url = img_tag.get("src", "")

        if image_url and not image_url.startswith("http"):
            image_url = "https://fantasiafestival.com" + image_url

    showtime = Showtime(parser.parse(event["exactTime"]))
    return Show(
        title=event["titre"],
        showtimes=[showtime],
        link=url,
        extra={
            "director": director,
            "country": country,
            "duration": duration,
            "description": description,
            "image": image_url,
        },
    )


def remove_dups(shows_list):
    unique_shows = {}
    for show in shows_list:
        unique_shows[(show.title, show.showtimes[0].datetime)] = show
    return list(unique_shows.values())


def main():
    shows = remove_dups(get_shows())
    shows_file = Path(__file__).parent / "shows.json"
    showlib.save(shows, shows_file, "Fantasia")


if __name__ == "__main__":
    main()
