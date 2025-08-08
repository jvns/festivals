from collections import defaultdict
from datetime import timedelta
from urllib.parse import quote
from jinja2 import Template
from src.generator import build_date_range, load_shows, copy_static_assets

FESTIVALS = [
    {"path": "src/fantasia-2025/shows.json", "name": "Fantasia", "color": "#8b0000"},
    {
        "path": "src/shakespeare-2025/shows.json",
        "name": "Shakespeare in the Park",
        "color": "#ff65c3"
    },
    {"path": "src/mutek-2025/shows.json", "name": "MUTEK", "color": "#ff6347"},
    {
        "path": "src/theatre-de-verdure-2025/shows.json",
        "name": "Theatre de Verdure",
        "color": "#228b22"
    },
    {"path": "src/fireworks-2025/shows.json", "name": "Fireworks", "color": "#4169e1"},
    {
        "path": "src/nuits-d-afrique-2025/shows.json",
        "name": "Nuits d'Afrique",
        "color": "#ff8c00"
    },
    {
        "path": "src/haiti-en-folie-2025/shows.json",
        "name": "Haïti en Folie",
        "color": "#dc143c"
    },
    {
        "path": "src/presence-autochtone-2025/shows.json",
        "name": "Présence Autochtone",
        "color": "#fb630b"
    },
    {"path": "src/wild-pride-2025/shows.json", "name": "Wild Pride", "color": "#fccaca"},
    {"path": "src/italfest-2025/shows.json", "name": "Italfest", "color": "#009639"},
]


def generate_google_calendar_link(event, festival_name):
    title = quote(f"{event['title']} ({festival_name})")
    start_time = event["datetime"].strftime("%Y%m%dT%H%M%S")
    end_time = (event["datetime"] + timedelta(hours=2)).strftime("%Y%m%dT%H%M%S")

    # Build description with event link first
    description_parts = [event["link"]]

    # Add event description if available
    if "description" in event and event["description"]:
        description_parts.append(event["description"])

    description = quote("\n\n".join(description_parts))

    url = f"https://calendar.google.com/calendar/u/0/r/eventedit?text={title}&dates={start_time}/{end_time}&details={description}"

    if "venue" in event and event["venue"] and event["venue"] != "TBD":
        location = quote(event["venue"])
        url += f"&location={location}"

    return url


def get_festival_date_range(festival_path):
    """Get the start and end dates for a festival from its JSON data."""
    try:
        events_by_date = load_shows(festival_path)
        if not events_by_date:
            return None, None
        
        dates = list(events_by_date.keys())
        start_date = min(dates)
        end_date = max(dates)
        return start_date, end_date
    except (FileNotFoundError, json.JSONDecodeError):
        return None, None


def get_festivals_metadata():
    """Get metadata for all festivals including date ranges."""
    festivals_metadata = []
    
    for festival_config in FESTIVALS:
        start_date, end_date = get_festival_date_range(festival_config["path"])
        
        # Create URL slug from festival name
        slug = festival_config["name"].lower().replace(' ', '-').replace("'", '').replace('ï', 'i').replace('é', 'e')
        if slug == "shakespeare-in-the-park":
            slug = "shakespeare"

        metadata = {
            "name": festival_config["name"],
            "slug": slug,
            "start_date": start_date,
            "end_date": end_date,
            "path": festival_config["path"],
            "color": festival_config.get("color")
        }
        festivals_metadata.append(metadata)
    
    return festivals_metadata


def load_shows_data():
    """Load all shows and group them by date and festival."""
    all_events_by_date = defaultdict(lambda: defaultdict(list))

    for festival_config in FESTIVALS:
        events_by_date = load_shows(festival_config["path"])
        festival_name = festival_config["name"]

        # Group events by date and festival
        for date, events in events_by_date.items():
            all_events_by_date[date][festival_name].extend(events)

    return all_events_by_date


def generate_html():
    with open("src/2025/template.html", "r", encoding="utf-8") as f:
        template_content = f.read()

    events_by_date = load_shows_data()
    calendar_dates = build_date_range(events_by_date)
    festivals_metadata = get_festivals_metadata()

    template = Template(template_content)
    return template.render(
        calendar_dates=calendar_dates,
        events_by_date=events_by_date,
        festivals_metadata=festivals_metadata,
        generate_google_calendar_link=generate_google_calendar_link,
    )


if __name__ == "__main__":
    # Copy static assets first
    copy_static_assets()
    
    # Generate main page HTML
    html = generate_html()
    with open("site/index.html", "w", encoding="utf-8") as f:
        f.write(html)
