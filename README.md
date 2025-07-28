# festivals.jvns.ca

This repository has a bunch of Python scripts that scrape Montreal festival
websites to generate a static HTML site.

## building

* `bash scripts/build.sh` rebuilds everything
* `bash scripts/watch.sh` rebuild automatically when files changes

You can rebuild just one festival by doing something like this:

```bash
export PYTHONPATH=.
python3 src/fantasia-2025/scrape.py
python3 src/fantasia-2025/generate.py
python3 src/generate.py  # Update main page too
```

# how it works

Here's an ASCII art diagram of the overall flow:

```
website → scraper → JSON → generator → HTML Calendar
                      ↓
          all JSON Files → generator → main page
```

### `shows.json` format

Here's an example:

```json
{
  "title": "C.R.A.Z.Y.",
  "showtimes": [
    {
      "datetime": "2025-07-16 19:30:00",
      "venue": "Parc Lafontaine"
    }
  ],
  "link": "https://example.com/crazy"
}
```

Notes:

* Dates must be formatted as `YYYY-MM-DD HH:MM:SS`. The `Showtime` class validates this. 
* Only the `title`, `link`, and `datetime` fields are required. `venue` will be
  displayed on the main page if it's included.
* Every other field is optional and festival-specific. Fantasia events have
  `duration` and `country`, Shakespeare in the Park has `park` and `city`, etc. 

### HTTP cache (`src/cache.py`)

When you fetch a URL, it stores the response in an SQLite database so we
don't have to re-download it. Sleeps for 0.1 seconds between requests for rate limiting.

## templates

There are these shared templates & styles:

- `src/2025/template.html`: The main combined page
- `src/2025/calendar-base.html`:e Base style for the individual festival pages
- `site/2025/calendar-base.css`: Base styles for calendars

Each festival has its own template (`calendar.html`) and CSS (`calendar.css`). `calendar.html` is in `src/` and `calendar.css` is in `site/` for whatever reason.

## Adding a new festival

1. Create the directory structure (`src/{festival-name-year}/`, `site/{year}/festival-name`)
2. Write the scraper (`scrape.py`), look at `src/fantasia-2025/scrape.py` for a good example. Key points:
3. Write `generate.py` (just 3 lines, copy one of the other `generate.py`s)
4. Write `calendar.html` and a `calendar.css`
5. Update the `scripts/build.sh` build script
6. Update the main page:
  - Add the festival to the `FESTIVALS` dict in `src/generate.py`
  - Add a navigation link in `src/2025/calendar-base.html`
