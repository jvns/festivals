from collections import defaultdict
from datetime import timedelta
from urllib.parse import quote
from jinja2 import Template
from src.generator import build_date_range, load_shows

FESTIVALS = [
    {"path": "src/fantasia-2025/shows.json", "name": "Fantasia"},
    {
        "path": "src/shakespeare-2025/shows.json",
        "name": "Shakespeare in the Park",
    },
    {"path": "src/mutek-2025/shows.json", "name": "MUTEK"},
    {
        "path": "src/theatre-de-verdure-2025/shows.json",
        "name": "Theatre de Verdure",
    },
    {"path": "src/fireworks-2025/shows.json", "name": "Fireworks"},
    {
        "path": "src/nuits-d-afrique-2025/shows.json",
        "name": "Nuits d'Afrique",
    },
    {
        "path": "src/haiti-en-folie-2025/shows.json",
        "name": "Haïti en Folie",
    },
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

    template = Template(template_content)
    return template.render(
        calendar_dates=calendar_dates,
        events_by_date=events_by_date,
        generate_google_calendar_link=generate_google_calendar_link,
    )


if __name__ == "__main__":
    html = generate_html()
    with open("site/index.html", "w", encoding="utf-8") as f:
        f.write(html)
