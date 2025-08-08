"""
ItalfestMTL scraper - fetches festival data
"""

import json
import re
from pathlib import Path

from dateutil import parser
from bs4 import BeautifulSoup

from src.cache import HTTPCache
import src.showlib as showlib
from src.showlib import Show, Showtime


def get_shows():
    cache = HTTPCache()
    
    url = "https://italfestmtl.ca/wp-json/wp/v2/evenements?per_page=100&lang=en"
    content = cache.fetch(url, timeout=10)
    events_data = json.loads(content)
    
    shows = []
    
    for event in events_data:
        title = event["title"]["rendered"]
        link = event["link"]

        # Extract content and parse event details
        content_html = event["content"]["rendered"]
        soup = BeautifulSoup(content_html, "html.parser")
        content_text = soup.get_text()

        # Parse event details from individual event page
        event_page = cache.fetch(link, timeout=10)
        event_soup = BeautifulSoup(event_page, "html.parser")

        # Parse date/time and venue from HTML selectors
        showtimes = parse_event_details_from_html(event_soup)
        if not showtimes:
            continue

        show = Show(
            title=title,
            showtimes=showtimes,
            link=link,
            extra={
                "description": content_text[:500] if content_text else "",
            },
        )
        shows.append(show)

    return shows


def parse_event_details_from_html(soup):
    """Parse event date/time and venue from HTML selectors."""
    
    dts = []
    venue = ""
    
    # Look for the Details section - find heading containing "Details"
    details_heading = soup.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], 
                               string=re.compile(r'Details', re.IGNORECASE))
    
    if details_heading:
        # Find the next ul element after the Details heading
        details_list = details_heading.find_next('ul')
        if details_list:
            list_items = details_list.find_all('li', limit=2)
            
            # First li: Date and time
            if len(list_items) > 0:
                date_time_text = list_items[0].get_text(separator=' ', strip=True)
                dts = parse_datetime_from_text(date_time_text)
            
            # Second li: Venue
            if len(list_items) > 1:
                venue_text = list_items[1].get_text(separator=' ', strip=True)
                venue = clean_venue_text(venue_text)

    return [Showtime(dt, venue) for dt in dts]

def parse_datetime_from_text(text):
    match = re.search(r"(August \d+(?:th)?,? 2025)", text)
    if not match:
        return []
    date = match[1]

    time_texts = text.split('and')
    times = []
    res = [
        r"\d+(:\d+)? [ap]\.?m\.?",
        r"\d+ h \d+",
    ]
    for time in time_texts:
        for r in res:
            match = re.search(r, time, flags=re.I)
            if match:
                times.append(match[0])
                break

    dts = []
    for time in times:
        dts.append(parser.parse(f"{date} {time}"))
    return dts


def clean_venue_text(text):
    # Remove long addresses
    return re.sub(r"\s+\d{3,}.*", "", text).strip()

def main():
    shows = get_shows()
    shows_file = Path(__file__).parent / "shows.json"
    showlib.save(shows, shows_file, "Italfest")


if __name__ == "__main__":
    main()