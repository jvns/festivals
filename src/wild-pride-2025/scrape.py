"""
Fetch Wild Pride program data from the website and convert to fringe format
"""

import re
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
        try:
            dt = parser.parse(date_text)

            extra_fields = {
                "location": location,
                "audience": audience,
                "price": price,
                "image": "",
                "organizer": organizer,
            }
            show = Show(
                title=title,
                showtimes=[Showtime(dt)],
                link=link,
                extra=extra_fields
            )
            shows.append(show)
        except:
            pass

    return shows

def main():
    shows = get_shows()
    shows_file = Path(__file__).parent / "shows.json"
    showlib.save(shows, shows_file, "Wild Pride")


if __name__ == "__main__":
    main()