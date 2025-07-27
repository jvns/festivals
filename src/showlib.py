"""
Module for managing show collections and saving to JSON
"""

import json
from datetime import datetime
from typing import List, Dict, Any


class Showtime:
    def __init__(self, datetime_obj, venue: str = "", extra=None):
        assert isinstance(
            datetime_obj, datetime
        ), f"Expected datetime object, got {type(datetime_obj)}"
        self.datetime = datetime_obj
        self.venue = venue
        self.extra = extra

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "datetime": self.datetime.strftime("%Y-%m-%d %H:%M:%S"),
        }
        if self.venue != '':
            result['venue'] = self.venue
        if self.extra is not None:
            result.update(self.extra)
        return result


class Show:
    def __init__(
        self,
        title: str,
        link: str,
        showtimes: List[Showtime],
        extra=None,
    ):
        self.title = title
        self.showtimes = showtimes
        self.link = link
        self.extra = extra

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "title": self.title,
            "showtimes": [showtime.to_dict() for showtime in self.showtimes],
            "link": self.link,
        }
        if self.extra is not None:
            result.update(self.extra)
        return result


def save(shows, filename, festival_name=None):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            [show.to_dict() for show in shows],
            f,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
        )

    if festival_name:
        print(f"{festival_name}: scraped {len(shows)} events")
