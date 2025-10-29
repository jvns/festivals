"""
Scraper for Festival Cinemania using their GraphQL API
"""

import json
from datetime import datetime
from pathlib import Path

from dateutil import parser

from src.cache import HTTPCache
import src.showlib as showlib
from src.showlib import Show, Showtime


def get_shows():
    cache = HTTPCache()

    # Get all dates in November 2025 for the festival
    from datetime import datetime, timedelta

    shows = []

    # Festival runs November 5-16, 2025
    start_date = datetime(2025, 11, 5)
    end_date = datetime(2025, 11, 16)

    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime("%Y-%m-%d")

        # GraphQL query to get programs for this specific date
        query = {
            "operationName": "listingPrograms",
            "variables": {
                "limit": 99,
                "lang": "en",
                "currentdate": ["and", f">= {date_str} 00:00:00", f"<= {date_str} 23:59:59"],
                "venue": None,
                "editionID": 10
            },
            "query": """query listingPrograms($lang: [String], $venue: [String], $editionID: [QueryArgument], $currentdate: [QueryArgument], $currentID: QueryArgument, $limit: Int = 99) {
  programs: entries(
    section: "program_zf"
    site: $lang
    relatedToEntries: [{slug: $venue, site: $lang}]
    program_edition_id: $editionID
    program_date_start: $currentdate
    limit: $limit
    id: ["not", $currentID]
    orderBy: "program_date_start ASC"
  ) {
    id
    url
    title
    program_ticket_url
    program_date_start
    select_venue {
      title
      venue_name
    }
    program_films(orderBy: "heure ASC") {
      heure
      film {
        id
        url
        title
        select_category {
          title
        }
        select_generic {
          generic_post
          generic_name_first
          generic_name_last
        }
        select_section {
          title
        }
        select_country {
          title
        }
        film_image {
          ... on film_image_bloc_film_image_BlockType {
            image {
              url
              alt
              title
            }
            principal
            poster
          }
        }
      }
    }
  }
}"""
        }

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:143.0) Gecko/20100101 Firefox/143.0',
            'Accept': '*/*',
            'Accept-Language': 'en-CA,en-US;q=0.7,en;q=0.3',
            'Referer': f'https://festivalcinemania.com/en/schedule?day={current_date.strftime("%A").lower()}-{current_date.strftime("%B").lower()}-{current_date.day}',
            'content-type': 'application/json',
            'Origin': 'https://festivalcinemania.com',
        }

        url = "https://festivalcinemania.com/graphql"

        # Create a cache key that includes the POST data
        import hashlib
        cache_key = url + "_POST_" + hashlib.md5(json.dumps(query).encode()).hexdigest()

        # Check cache first
        cached = cache.get(cache_key)
        if cached:
            content = cached
        else:
            # Make POST request
            import requests
            import time
            response = requests.post(url, json=query, headers=headers, timeout=10)
            time.sleep(0.1)  # Rate limiting
            response.raise_for_status()
            content = response.text
            cache.put(cache_key, content)

        data = json.loads(content)

        if data and 'data' in data and 'programs' in data['data']:
            for program in data['data']['programs']:
                try:
                    program_shows = process_program(program)
                    shows.extend(program_shows)
                except Exception as e:
                    print(f"Error processing program {program.get('title', 'Unknown')}: {e}")
                    continue

        current_date += timedelta(days=1)

    return shows


def process_program(program):
    """Convert a program from the API into Show objects"""
    shows = []

    program_date = program.get('program_date_start')
    ticket_url = program.get('program_ticket_url', '')

    # Get venue
    venue_name = ""
    if program.get('select_venue'):
        venues = program['select_venue']
        if venues:
            venue = venues[0] if isinstance(venues, list) else venues
            venue_name = venue.get('venue_name') or venue.get('title', '')

    # Check if this is a multi-film program (like short film collections)
    program_films = program.get('program_films', [])

    if len(program_films) > 1:
        # This is a multi-film program - create one event for the entire program
        program_title = program['title']
        program_url = program['url']

        # Collect info from all films for the description
        film_titles = []
        directors = set()
        countries = set()
        categories = set()

        for film_entry in program_films:
            films = film_entry.get('film', [])
            if not films:
                continue

            film = films[0] if isinstance(films, list) else films
            film_titles.append(film.get('title', ''))

            # Collect directors
            for person in film.get('select_generic', []):
                if person.get('generic_post') in ['Réalisateur', 'Réalisatrice', 'Director']:
                    first_name = person.get('generic_name_first', '')
                    last_name = person.get('generic_name_last', '')
                    full_name = f"{first_name} {last_name}".strip()
                    if full_name:
                        directors.add(full_name)

            # Collect countries
            for country in film.get('select_country', []):
                countries.add(country['title'])

            # Collect categories
            for cat in film.get('select_category', []):
                categories.add(cat['title'])

        extra = {}
        if directors:
            extra['director'] = ', '.join(sorted(directors))
        if countries:
            extra['country'] = ', '.join(sorted(countries))
        if categories:
            extra['category'] = ', '.join(sorted(categories))
        if ticket_url:
            extra['ticket_url'] = ticket_url

        # Add film list to description
        extra['films'] = film_titles

        # Use program start time
        if program_date:
            try:
                program_dt = parser.parse(program_date)
                showtime = Showtime(program_dt, venue_name)

                show = Show(
                    title=program_title,
                    showtimes=[showtime],
                    link=program_url,
                    extra=extra if extra else None
                )
                shows.append(show)

            except Exception as e:
                print(f"Error parsing program datetime {program_date}: {e}")

    else:
        # Single film program - process as individual film
        for film_entry in program_films:
            films = film_entry.get('film', [])
            if not films:
                continue

            film = films[0] if isinstance(films, list) else films

            title = film['title']
            url = film['url']
            extra = {}

            # Get category
            categories = film.get('select_category', [])
            if categories:
                extra['category'] = categories[0]['title']

            # Get section
            sections = film.get('select_section', [])
            if sections:
                extra['section'] = sections[0]['title']

            # Get country
            countries = [country['title'] for country in film.get('select_country', [])]
            if countries:
                extra['country'] = ', '.join(countries)

            # Get director(s)
            directors = []
            for person in film.get('select_generic', []):
                if person.get('generic_post') in ['Réalisateur', 'Réalisatrice', 'Director']:
                    first_name = person.get('generic_name_first', '')
                    last_name = person.get('generic_name_last', '')
                    full_name = f"{first_name} {last_name}".strip()
                    if full_name:
                        directors.append(full_name)
            if directors:
                extra['director'] = ', '.join(directors)

            # Get image
            for img_block in film.get('film_image', []):
                if img_block.get('poster') and img_block.get('image'):
                    images = img_block['image']
                    if images:
                        image = images[0] if isinstance(images, list) else images
                        extra['image'] = image['url']
                        break
                # Fallback to any image if no poster
                elif img_block.get('image'):
                    images = img_block['image']
                    if images:
                        image = images[0] if isinstance(images, list) else images
                        extra['image'] = image['url']
                        break

            # Add ticket URL if available
            if ticket_url:
                extra['ticket_url'] = ticket_url

            # Get showtime
            time_str = film_entry.get('heure')
            if time_str and program_date:
                try:
                    # Parse the time from heure field
                    time_dt = parser.parse(time_str)
                    # Parse the program date
                    program_dt = parser.parse(program_date)
                    # Combine the correct date with the time
                    combined_dt = program_dt.replace(
                        hour=time_dt.hour,
                        minute=time_dt.minute,
                        second=time_dt.second
                    )
                    showtime = Showtime(combined_dt, venue_name)

                    show = Show(
                        title=title,
                        showtimes=[showtime],
                        link=url,
                        extra=extra if extra else None
                    )
                    shows.append(show)

                except Exception as e:
                    print(f"Error parsing datetime program_date={program_date}, time={time_str}: {e}")
                    continue

    return shows


def main():
    shows = get_shows()
    shows_file = Path(__file__).parent / "shows.json"
    showlib.save(shows, shows_file, "Cinemania")


if __name__ == "__main__":
    main()
