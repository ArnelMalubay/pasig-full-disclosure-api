"""
Utility functions for the Pasig Full Disclosure API.

This module provides functions for fetching, caching, and managing HTML data
from the Pasig City government website. HTML content is stored in Vercel Blob,
while timestamp metadata is stored in Vercel KV (Redis). All timestamps use UTC+8.
"""

import requests
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict

# Vercel KV (Redis) client
from redis import Redis

# Vercel Blob client
from vercel_blob import Blob


# Initialize KV + Blob clients
kv = Redis.from_url(os.getenv["REDIS_URL"], decode_responses=True)
blob = Blob(token = os.getenv["BLOB_READ_WRITE_TOKEN"])


# Mapping of data paths to their corresponding URLs on the Pasig City website
path_to_url: Dict[str, str] = {
    "resolutions": "https://pasigcity.gov.ph/city-resolutions",
    "ordinances": "https://pasigcity.gov.ph/city-ordinances",
    "executive-orders": "https://pasigcity.gov.ph/executive-orders",
    "bids-and-awards": "https://pasigcity.gov.ph/bids-and-awards",
}


def refresh_html(path: str) -> None:
    """
    Fetch HTML content from the Pasig City website and store it in Vercel Blob.

    Args:
        path: The data path (e.g. 'resolutions', 'ordinances', etc.).
              Must be a key in the path_to_url dictionary.

    Returns:
        None

    Side Effects:
        - Uploads or overwrites `html/{path}.html` in Vercel Blob storage.
    """
    url = path_to_url[path]
    html = requests.get(url)

    # Upload HTML to Blob (stored as html/resolutions.html, etc.)
    blob.put(
        path=f"html/{path}.html",
        data=html.text.encode("utf-8"),
        content_type="text/html",
    )


def update_time(path: str) -> None:
    """
    Update the last refresh timestamp for a specific data path in UTC+8.

    This function stores the timestamp for the given path in Vercel KV.

    Args:
        path: The data path to update.

    Returns:
        None

    Side Effects:
        - Updates the timestamp in Redis KV.
    """
    utc_plus_8 = timezone(timedelta(hours=8))
    current_time = datetime.now(utc_plus_8).isoformat()

    kv.set(f"time:{path}", current_time)


def get_time(path: str) -> Optional[str]:
    """
    Retrieve the last refresh timestamp for a specific data path from Vercel KV.

    Args:
        path: The data path to look up.

    Returns:
        ISO-format timestamp string, or None if not found.
    """
    return kv.get(f"time:{path}")


def get_html(path: str) -> Optional[str]:
    """
    Retrieve cached HTML content from Vercel Blob.

    Args:
        path: The data path (e.g. 'resolutions').

    Returns:
        The HTML content as a string, or None if the file does not exist.
    """
    try:
        file = blob.get(f"html/{path}.html")
        return file.read().decode("utf-8")
    except Exception:
        return None  # File does not exist in Blob


def update_if_needed(path: str, refresh_timer: timedelta = timedelta(days=1)) -> None:
    """
    Refresh HTML content if the cached version is outdated. Uses Blob for HTML
    and KV for timestamps.

    This function checks the timestamp stored in KV and refreshes the cached
    HTML if it is older than `refresh_timer`. If no timestamp exists, a refresh
    is performed immediately.

    Args:
        path: The data path to validate.
        refresh_timer: Minimum time between refreshes (default: 1 day).

    Returns:
        None

    Side Effects:
        - May fetch new HTML content and upload it to Blob.
        - May update the timestamp in KV.
    """
    last_updated_str = get_time(path)

    # No prior record → refresh immediately
    if last_updated_str is None:
        refresh_html(path)
        update_time(path)
        return

    # Parse stored timestamp
    last_updated = datetime.fromisoformat(last_updated_str)

    # Current time in UTC+8
    utc_plus_8 = timezone(timedelta(hours=8))
    current_time = datetime.now(utc_plus_8)

    # Determine if refresh is needed
    if current_time - last_updated >= refresh_timer:
        refresh_html(path)
        update_time(path)

    return


def get_current_year() -> int:
    """
    Get the current year in UTC+8 (Philippine time), regardless of server location.

    Returns:
        The current year as an integer.
    """
    utc_plus_8 = timezone(timedelta(hours=8))
    current_time = datetime.now(utc_plus_8)
    return current_time.year