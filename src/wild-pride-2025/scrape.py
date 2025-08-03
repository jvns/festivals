"""
Fetch Wild Pride program data from the website and convert to fringe format
"""

import re
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from src.cache import HTTPCache
import src.showlib as showlib
from src.showlib import Show, Showtime

def get_shows():
    cache = HTTPCache()
    shows = []

    url = "https://wildpride.ca"
    content = cache.fetch(url, timeout=10)
    content = content.encode('latin-1').decode('utf-8')
    soup = BeautifulSoup(content, "html.parser")

    events_div = soup.find("div", class_="bcontent")
    event_elements = events_div.find_all(recursive=False)

    for i in range(0, len(event_elements), 2):
        if i + 1 >= len(event_elements):
            break

        h3 = event_elements[i]
        div = event_elements[i + 1]

        if h3.name != 'h3' or div.name != 'div':
            continue

        link_elem = h3.find('a')
        title_text = h3.get_text()

        link = urljoin(url, link_elem['href'])
        title = link_elem.get_text().strip()

        # Extract organizer from text after the link in h3
        organizer = ""
        for sibling in link_elem.next_siblings:
            if hasattr(sibling, 'strip'):
                organizer += sibling.strip()
        organizer = re.sub(r'^\s*by\s+', '', organizer)

        details = div.get_text().strip().split('\n')
        date_text, location, audience, price = [d.strip() for d in details]

        showtimes = parse_dates(date_text, location)
        if showtimes:
            extra_fields = {
                "location": location,
                "audience": audience,
                "price": price,
                "image": "",
                "organizer": organizer,
            }
            show = Show(
                title=title,
                showtimes=showtimes,
                link=link,
                extra=extra_fields
            )
            shows.append(show)

    return shows

def parse_time(time_str):
    if time_str == 'midnight':
        return 0, 0
    elif ':' in time_str:
        time_match = re.match(r'(\d+):(\d+)h', time_str)
        return int(time_match.group(1)), int(time_match.group(2))
    else:
        time_match = re.match(r'(\d+)h(\d+)?', time_str)
        hour = int(time_match.group(1))
        minute = int(time_match.group(2)) if time_match.group(2) else 0
        return hour, minute

def extract_days(date_part):
    # Handle patterns like "1,8, and 15" or "1, August 8, and August 15"
    tokens = re.split(r',\s*(?:and\s+)?|\s+and\s+', date_part)
    days = []
    for token in tokens:
        # Extract all numbers from each token
        day_matches = re.findall(r'\b(\d+)\b', token.strip())
        for day_str in day_matches:
            days.append(int(day_str))
    return days

def format_time(hour, minute):
    return f"{hour:02d}:{minute:02d}"

# Dates and times are in a panoply of inconsistent formats, what a disaster!
def parse_dates(date_text, venue):
    if 'register to find out time' in date_text.lower() or 'tba' in date_text.lower():
        return []

    month_map = {
        'January': 1, 'February': 2, 'March': 3, 'April': 4, 'May': 5, 'June': 6,
        'July': 7, 'August': 8, 'September': 9, 'October': 10, 'November': 11, 'December': 12
    }

    # Smart segmentation: split on new months, but keep single month patterns together
    if re.search(r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+,\s*(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+.*(?:at|from)', date_text):
        segments = [date_text]  # Keep patterns like "Aug 1, Aug 8, and Aug 15 at 15h" together
    else:
        segments = re.split(r',\s*(?=(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+)', date_text)

    showtimes = []
    for segment in segments:
        # Extract time info (prioritize show times over doors)
        time_patterns = [
            (r'show starts at (\d+h\d*)', None),
            (r'\(.*?starts at (\d+h\d*)\)', None),
            (r'show\s+at\s+(\d+h\d*)', None),
            (r'(\d+h\d*)\s+to\s+midnight', 'midnight'),
            (r'from\s+(\d+h\d*)\s+to\s+(\d+h\d*|midnight)', 'range'),
            (r'(\d+h\d*)\s+to\s+(\d+h\d*|midnight)', 'range'),
            (r'at\s+(\d+h\d*|\d+:\d+h)', None),
            (r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d+\s+(\d+h\d*)', None)
        ]

        start_time = end_time = None
        # Special case: if we have parenthetical start time, also check for range end time
        paren_match = re.search(r'\(.*?starts at (\d+h\d*)\)', segment)
        range_match = re.search(r'from\s+\d+h\d*\s+to\s+(\d+h\d*|midnight)', segment)

        if paren_match and range_match:
            start_time = paren_match.group(1)
            end_time = range_match.group(1)
        else:
            for pattern, ptype in time_patterns:
                match = re.search(pattern, segment)
                if match:
                    start_time = match.group(1)
                    if ptype == 'range':
                        end_time = match.group(2)
                    elif ptype == 'midnight':
                        end_time = 'midnight'
                    else:
                        end_time = None
                    break

        if not start_time:
            continue

        # Extract date part - everything from month until time keyword
        date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(.*?)(?:\s+(?:at|from|show\s+at)\s+\d+h|\s+\d+h\s*(?:to|\s*$))', segment)
        if not date_match:
            # Fallback for direct time patterns like "August 3 17h"
            date_match = re.search(r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d+)', segment)

        if not date_match:
            continue

        month_name, date_part = date_match.groups()
        month = month_map[month_name]
        days = extract_days(date_part)
        hour, minute = parse_time(start_time)

        for day in days:
            dt = datetime(2025, month, day, hour, minute)
            extra = None
            if end_time:
                end_hour, end_minute = parse_time(end_time)
                extra = {'end_time': format_time(end_hour, end_minute)}
            showtimes.append(Showtime(dt, venue, extra))

    return showtimes

def test_parse_dates():
    test_cases = [
        ("July 30 at 17h30", "My venue", [
            Showtime(datetime(2025, 7, 30, 17, 30), "My venue")
        ]),
        ("August 1 to August 10", "My venue", []),
        ("July 31 from 19h to 20h30", "My venue", [
            Showtime(datetime(2025, 7, 31, 19), "My venue", {'end_time': "20:30"})
        ]),
        ("July 31 at 20h30, August 1 at 20h30", "My venue", [
            Showtime(datetime(2025, 7, 31, 20, 30), "My venue"),
            Showtime(datetime(2025, 8, 1, 20, 30), "My venue")
        ]),
        ("August 1, doors at 19h show at 20h", "My venue", [
            Showtime(datetime(2025, 8, 1, 20), "My venue"),
        ]),
        ("August 1,8, and 15 at 16h to 20h, August 2 and 9 at 12h to 17h, August 5 at 14h to 19h", "My venue", [
            Showtime(datetime(2025, 8, 1, 16), "My venue", {'end_time': "20:00"}),
            Showtime(datetime(2025, 8, 8, 16), "My venue", {'end_time': "20:00"}),
            Showtime(datetime(2025, 8, 15, 16), "My venue", {'end_time': "20:00"}),
            Showtime(datetime(2025, 8, 2, 12), "My venue", {'end_time': "17:00"}),
            Showtime(datetime(2025, 8, 9, 12), "My venue", {'end_time': "17:00"}),
            Showtime(datetime(2025, 8, 5, 14), "My venue", {'end_time': "19:00"}),
        ]),
        ("August 2 at 9:45h", "My venue", [
            Showtime(datetime(2025, 8, 2, 9, 45), "My venue")
        ]),
        ("August 8, register to find out time", "My venue", []),
        ("July 31 from 20h to 2h", "My venue", [
            Showtime(datetime(2025, 7, 31, 20), "My venue", {'end_time': "02:00"})
        ]),
        ("August 1, August 8, and August 15 at 15h", "My venue", [
            Showtime(datetime(2025, 8, 1, 15), "My venue"),
            Showtime(datetime(2025, 8, 8, 15), "My venue"),
            Showtime(datetime(2025, 8, 15, 15), "My venue")
        ]),
        ("August 3 17h to 20h", "My venue", [
            Showtime(datetime(2025, 8, 3, 17), "My venue", {'end_time': "20:00"}),
        ]),
        ("August 3 17h", "My venue", [
            Showtime(datetime(2025, 8, 3, 17), "My venue"),
        ]),
        ("August 7 at 19h30, show starts at 20h", "My venue", [
            Showtime(datetime(2025, 8, 7, 20), "My venue"),
        ]),
        ("August 13 from 17h30 to 21h (concert starts at 19h)", "My venue", [
            Showtime(datetime(2025, 8, 13, 19), "My venue", {'end_time': "21:00"}),
        ]),
        ("August 16, 20h to midnight", "My venue", [
            Showtime(datetime(2025, 8, 16, 20), "My venue", {'end_time': "00:00"}),
        ]),
    ]

    for i, (date_text, venue, expected) in enumerate(test_cases):
        result = parse_dates(date_text, venue)
        if result != expected:
            print(f"Test {i+1}: FAIL")
            print(f"  Input: {date_text}")
            print(f"  Expected: {expected}")
            print(f"  Got: {result}")

def main():
    shows = get_shows()
    shows_file = Path(__file__).parent / "shows.json"
    showlib.save(shows, shows_file, "Wild Pride")


if __name__ == "__main__":
    if len(__import__('sys').argv) > 1 and __import__('sys').argv[1] == 'test':
        test_parse_dates()
    else:
        main()