"""
Scraper for Haiti en Folie festival 2025
https://montreal.haitienfolie.com/wp-json/festival/v1/events?per_page=100
"""

import json
from pathlib import Path
from datetime import datetime

from dateutil import parser

from src.cache import HTTPCache
import src.showlib as showlib
from src.showlib import Show, Showtime


def scrape_haiti_en_folie_data():
    cache = HTTPCache()
    url = "https://montreal.haitienfolie.com/wp-json/festival/v1/events?per_page=100"
    content = cache.fetch(url, timeout=10)
    data = json.loads(content)
    
    
    shows = []
    
    # Handle different response structures
    events = data
    venues = {}
    if isinstance(data, dict):
        # If response is wrapped in an object, look for events array
        events = data.get('event', data.get('events', data.get('data', [])))
        
        # Build venue mapping from place data
        places = data.get('place', [])
        for place in places:
            venue_id = place.get('id', '')
            venue_name = place.get('title', '')
            if venue_id and venue_name:
                venues[venue_id] = venue_name
    
    for event in events:
        try:
            # Only process 2025 events
            if not event.get('date', '').startswith('2025'):
                continue
                
            show = parse_event(event, venues)
            if show:
                shows.append(show)
        except Exception:
            print("Error processing event:")
            print(json.dumps(event, indent=2))
            raise
    
    return shows


def parse_event(event, venues=None):
    """Parse an event from the API response"""
    if venues is None:
        venues = {}
    title = event.get('title', '').strip()
    if not title:
        return None
    
    # Parse date and time
    date_str = event.get('date', '')
    time_str = event.get('start_time', '')
    
    if not date_str or not time_str:
        return None
    
    try:
        # Combine date and time strings
        datetime_str = f"{date_str} {time_str}"
        dt = parser.parse(datetime_str)
    except:
        return None
    
    # Extract venue information
    venue_id = event.get('venue_id', '')
    venue = venues.get(venue_id, venue_id)  # Use venue name if available, fallback to venue_id
    if venue == 'EN LIGNE':
        return None
    
    # Event URL - use the correct URL format with wp_post_id
    wp_post_id = event.get('wp_post_id', '')
    link = f"https://montreal.haitienfolie.com/index.php?p={wp_post_id}" if wp_post_id else ""
    
    # Description
    description = event.get('description', '').strip()
    
    # Build extra data
    extra = {
        "festival": "Haïti en Folie"
    }
    
    if description:
        extra["description"] = description
    
    # Add subtitle if available
    sub_title = event.get('sub_title', '').strip()
    if sub_title:
        extra["sub_title"] = sub_title
    
    # Add subject if available
    subject = event.get('subject', '').strip() 
    if subject:
        extra["subject"] = subject
    
    # Add event type
    event_type = event.get('type', '').strip()
    if event_type:
        extra["type"] = event_type
    
    # Add images
    photo_small = event.get('photo_small', '')
    if photo_small:
        extra["image"] = photo_small
    
    photo_big = event.get('photo_big', '')
    if photo_big:
        extra["image_large"] = photo_big
    
    showtime = Showtime(dt, venue)
    
    return Show(
        title=title,
        showtimes=[showtime],
        link=link,
        extra=extra
    )


def main():
    shows = scrape_haiti_en_folie_data()
    shows_file = Path(__file__).parent / "shows.json"
    showlib.save(shows, shows_file, "Haiti en Folie")


if __name__ == "__main__":
    main()
