import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

from jinja2 import Environment, FileSystemLoader
from bs4 import BeautifulSoup


def build_date_range(events_by_date):
    start_date = min(events_by_date.keys())
    end_date = max(events_by_date.keys())

    calendar_dates = []
    current = start_date
    while current <= end_date:
        calendar_dates.append(current)
        current += timedelta(days=1)

    return calendar_dates


def flatten(events):
    # Get one item per showtime
    for event in events:
        for showtime in event["showtimes"]:
            dt = datetime.strptime(showtime["datetime"], "%Y-%m-%d %H:%M:%S")
            event_entry = event.copy()
            event_entry["datetime"] = dt
            event_entry["time"] = dt.strftime("%H:%M")

            # Add showtime-specific fields
            for key, value in showtime.items():
                if key != "datetime":
                    event_entry[key] = value
            yield event_entry


def load_shows(shows_json_path):
    with open(shows_json_path, "r", encoding="utf-8") as f:
        events = flatten(json.load(f))
    events = sorted(events, key=lambda x: x["datetime"])
    events_by_date = defaultdict(list)
    for e in events:
        events_by_date[e["datetime"].date()].append(e)
    return events_by_date


def copy_static_assets():
    """Copy static assets from src/static to site/"""
    static_dir = Path("src/static")
    site_dir = Path("site")
    
    if static_dir.exists():
        # Copy images
        if (static_dir / "images").exists():
            os.makedirs(site_dir / "images", exist_ok=True)
            shutil.copytree(static_dir / "images", site_dir / "images", dirs_exist_ok=True)
        
        # Copy 2025 static files
        if (static_dir / "2025").exists():
            os.makedirs(site_dir / "2025", exist_ok=True)
            for file in (static_dir / "2025").glob("*"):
                if file.is_file():
                    if file.name == "style.css":
                        # Main page style.css goes to site root
                        shutil.copy2(file, site_dir / "style.css")
                    else:
                        # Other files like calendar-base.css go to site/2025/
                        shutil.copy2(file, site_dir / "2025" / file.name)


def copy_festival_assets(festival_src_dir, festival_output_dir):
    """Copy festival-specific CSS and other assets"""
    festival_path = Path(festival_src_dir)
    output_path = Path(festival_output_dir)
    
    # Copy calendar.css if it exists
    css_file = festival_path / "calendar.css"
    if css_file.exists():
        os.makedirs(output_path, exist_ok=True)
        shutil.copy2(css_file, output_path / "calendar.css")


def render_calendar(calendar_html_path, shows_json_path, output_dir):
    # Load and organize shows
    events_by_date = load_shows(shows_json_path)

    # Generate calendar date range from the events
    calendar_dates = build_date_range(events_by_date)

    # Set up Jinja2 template rendering
    template_path = Path(calendar_html_path)
    env = Environment(
        loader=FileSystemLoader(
            [
                template_path.parent,
                template_path.parent / ".." / "2025",
            ]
        ),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("calendar.html")

    html = template.render(
        events_by_date=events_by_date,
        calendar_dates=calendar_dates,
        start_weekday=calendar_dates[0].weekday(),
    )
    soup = BeautifulSoup(html, "html.parser")
    html = soup.prettify()

    # Write output
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "index.html")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    # Copy festival-specific assets
    festival_src_dir = template_path.parent
    copy_festival_assets(festival_src_dir, output_dir)

    total_events = sum(len(events) for events in events_by_date.values())
    print(
        f"Generated calendar: {output_file} - {total_events} events across {len(calendar_dates)} days"
    )
