"""
Fetch Wild Pride program data from the website and convert to fringe format
"""

import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dateutil import parser

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
        
        if link_elem:
            link = urljoin(url, link_elem['href'])
            title = link_elem.get_text().strip()
        else:
            link = ""
            title = title_text.split(' by ')[0].strip()
            
        details = div.get_text().strip().split('\n')
        details = [d.strip() for d in details if d.strip()]
        
        date_time = details[0] if len(details) > 0 else ""
        location = details[1] if len(details) > 1 else ""
        audience = details[2] if len(details) > 2 else ""
        price = details[3] if len(details) > 3 else ""
        
        try:
            import re
            # Extract start time from ranges like "19h to 22h" or "from 19h to 22h"
            time_range = re.search(r'(?:from\s+)?(\d{1,2})h(?:\d{2})?\s+to\s+\d{1,2}h', date_time)
            if time_range:
                start_hour = int(time_range.group(1))
                date_part = re.search(r'(July|August)\s+\d{1,2}', date_time)
                if date_part:
                    dt = parser.parse(f"{date_part.group(0)} {start_hour}:00", fuzzy=True)
                else:
                    dt = datetime(2025, 8, 1, start_hour, 0)
            else:
                dt = parser.parse(date_time, fuzzy=True)
        except:
            dt = datetime(2025, 8, 1, 12, 0)
            
        show = Show(
            title=title,
            showtimes=[Showtime(dt)],
            link=link,
            extra={
                "location": location,
                "audience": audience,
                "price": price,
                "image": ""
            }
        )
        shows.append(show)

    return shows

def main():
    shows = get_shows()
    shows_file = Path(__file__).parent / "shows.json"
    showlib.save(shows, shows_file, "Wild Pride")


if __name__ == "__main__":
    main()