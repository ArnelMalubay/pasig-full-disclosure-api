# """
# Utility functions for the Pasig Full Disclosure API.

# This module provides functions for fetching, caching, and managing HTML data
# from the Pasig City government website. HTML content is stored in Vercel Blob,
# while timestamp metadata is stored in Vercel KV (Redis). All timestamps use UTC+8.
# """

# import requests
# import os
# from datetime import datetime, timezone, timedelta
# from typing import Optional, Dict

# # Vercel KV (Redis) client
# from redis import Redis

# # Vercel Blob client
# import vercel_blob as Blob


# # Initialize KV + Blob clients
# kv = Redis.from_url(os.getenv("REDIS_URL"), decode_responses = True)
# os.getenv("BLOB_READ_WRITE_TOKEN")


# # Mapping of data paths to their corresponding URLs on the Pasig City website
# path_to_url: Dict[str, str] = {
#     "resolutions": "https://pasigcity.gov.ph/city-resolutions",
#     "ordinances": "https://pasigcity.gov.ph/city-ordinances",
#     "executive-orders": "https://pasigcity.gov.ph/executive-orders",
#     "bids-and-awards": "https://pasigcity.gov.ph/bids-and-awards",
# }


# def refresh_html(path: str) -> None:
#     """
#     Fetch HTML content from the Pasig City website and store it in Vercel Blob.

#     Args:
#         path: The data path (e.g. 'resolutions', 'ordinances', etc.).
#               Must be a key in the path_to_url dictionary.

#     Returns:
#         None

#     Side Effects:
#         - Uploads or overwrites `html/{path}.html` in Vercel Blob storage.
#     """
#     url = path_to_url[path]
#     html = requests.get(url)

#     # Upload HTML to Blob (stored as html/resolutions.html, etc.)
#     Blob.put(
#         f"html/{path}.html",
#         html.text.encode("utf-8")
#     )


# def update_time(path: str) -> None:
#     """
#     Update the last refresh timestamp for a specific data path in UTC+8.

#     This function stores the timestamp for the given path in Vercel KV.

#     Args:
#         path: The data path to update.

#     Returns:
#         None

#     Side Effects:
#         - Updates the timestamp in Redis KV.
#     """
#     utc_plus_8 = timezone(timedelta(hours=8))
#     current_time = datetime.now(utc_plus_8).isoformat()

#     kv.set(f"time:{path}", current_time)


# def get_time(path: str) -> Optional[str]:
#     """
#     Retrieve the last refresh timestamp for a specific data path from Vercel KV.

#     Args:
#         path: The data path to look up.

#     Returns:
#         ISO-format timestamp string, or None if not found.
#     """
#     return kv.get(f"time:{path}")


# def get_html(path: str) -> Optional[str]:
#     """
#     Retrieve cached HTML content from Vercel Blob.

#     Args:
#         path: The data path (e.g. 'resolutions').

#     Returns:
#         The HTML content as a string, or None if the file does not exist.
#     """
#     try:
#         file = blob.get(f"html/{path}.html")
#         return file.read().decode("utf-8")
#     except Exception:
#         return None  # File does not exist in Blob


# def update_if_needed(path: str, refresh_timer: timedelta = timedelta(days=1)) -> None:
#     """
#     Refresh HTML content if the cached version is outdated. Uses Blob for HTML
#     and KV for timestamps.

#     This function checks the timestamp stored in KV and refreshes the cached
#     HTML if it is older than `refresh_timer`. If no timestamp exists, a refresh
#     is performed immediately.

#     Args:
#         path: The data path to validate.
#         refresh_timer: Minimum time between refreshes (default: 1 day).

#     Returns:
#         None

#     Side Effects:
#         - May fetch new HTML content and upload it to Blob.
#         - May update the timestamp in KV.
#     """
#     last_updated_str = get_time(path)

#     # No prior record → refresh immediately
#     if last_updated_str is None:
#         refresh_html(path)
#         update_time(path)
#         return

#     # Parse stored timestamp
#     last_updated = datetime.fromisoformat(last_updated_str)

#     # Current time in UTC+8
#     utc_plus_8 = timezone(timedelta(hours=8))
#     current_time = datetime.now(utc_plus_8)

#     # Determine if refresh is needed
#     if current_time - last_updated >= refresh_timer:
#         refresh_html(path)
#         update_time(path)

#     return


# def get_current_year() -> int:
#     """
#     Get the current year in UTC+8 (Philippine time), regardless of server location.

#     Returns:
#         The current year as an integer.
#     """
#     utc_plus_8 = timezone(timedelta(hours=8))
#     current_time = datetime.now(utc_plus_8)
#     return current_time.year



# V2

"""
Utility functions for the Pasig Full Disclosure API.

This module provides functions for fetching, caching, and managing HTML data
from the Pasig City government website. All timestamps use UTC+8 (Philippine Time).

Storage strategy used here:
- Timestamps are stored in Vercel KV (Redis compatible) to avoid Redis "maxmemory" issues
  for large blobs.
- HTML content is stored in Vercel Blob (object storage). We store the blob URL in KV
  so serverless functions can fetch the blob via HTTP (fast, edge-cached).

Notes / requirements:
- Install dependencies: `pip install requests redis vercel_blob` (vercel_blob is an
  unofficial Python wrapper; if you prefer, you can implement the HTTP calls yourself
  following the Vercel docs). If you don't want to use the unofficial package,
  comment out the `vercel_blob` usage and rely on public blob URLs stored in KV.
- Set these environment variables in your Vercel project (or locally with `vercel env pull`):
    - REDIS_URL           -> the Vercel KV Redis URL
    - BLOB_READ_WRITE_TOKEN -> the BLOB read-write token created for your blob store

Behavioral choices / rationale:
- When uploading to Blob we set the blob to be public so server-side reads can be
  done with a simple HTTP GET to the returned `url`. This keeps serverless memory
  usage low and avoids trying to store large HTML strings inside Redis.
- We keep every HTML blob filename as `<path>.html` so it is easy to identify in the
  blob store. We persist the public URL in KV under `blob_url:{path}`.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict
import os
import requests
import logging

# Try to import the unofficial vercel_blob package. If it's unavailable we will
# fall back to uploading via the Vercel CLI or other mechanism (see comments below).
try:
    import vercel_blob
    _HAS_VERCEL_BLOB = True
except Exception:
    vercel_blob = None
    _HAS_VERCEL_BLOB = False

# Redis client for Vercel KV (uses REDIS_URL environment variable)
from redis import Redis
kv = Redis.from_url(os.environ.get("REDIS_URL"), decode_responses=True)  # type: ignore

# Blob token (the BLOB_READ_WRITE_TOKEN created from the Vercel dashboard)
BLOB_TOKEN = os.environ.get("BLOB_READ_WRITE_TOKEN")

# Mapping of data paths to their corresponding URLs on the Pasig City website
path_to_url: Dict[str, str] = {
    "resolutions": "https://pasigcity.gov.ph/city-resolutions",
    "ordinances": "https://pasigcity.gov.ph/city-ordinances",
    "executive-orders": "https://pasigcity.gov.ph/executive-orders",
    "bids-and-awards": "https://pasigcity.gov.ph/bids-and-awards",
}


def _upload_blob_bytes(pathname: str, data: bytes, add_random_suffix: bool = False) -> Dict:
    """
    Upload bytes to Vercel Blob using the unofficial `vercel_blob` library.

    Returns the JSON-like response from the upload which usually contains at least
    a `url` and `pathname` field. Raises RuntimeError if upload fails or the
    environment isn't configured.

    Note: If you prefer not to use the unofficial wrapper, you can implement the
    server-side upload using the Vercel REST/SDK. The wrapper simplifies the
    example and maps closely to the official JS SDK surface.
    """
    if not _HAS_VERCEL_BLOB:
        raise RuntimeError("vercel_blob package not installed. Install it or implement HTTP upload.")
    if not BLOB_TOKEN:
        raise RuntimeError("BLOB_READ_WRITE_TOKEN is not set in environment.")

    options = {}
    if add_random_suffix:
        options["addRandomSuffix"] = "true"
    # Make the blob publicly accessible so we can fetch it via HTTP GET
    options["access"] = "public"

    # vercel_blob.put expects (pathname, bytes, options?)
    resp = vercel_blob.put(pathname, data, options)
    if not resp or not isinstance(resp, dict):
        raise RuntimeError("Unexpected response from vercel_blob.put: %r" % (resp,))
    return resp


def refresh_html(path: str) -> str:
    """
    Fetch HTML content from the Pasig City website and upload it to Vercel Blob.

    Args:
        path: The data path (e.g., 'resolutions', 'ordinances', 'executive-orders', 'bids-and-awards').
              Must be a key in the path_to_url dictionary.

    Returns:
        The public blob URL where the HTML was uploaded.

    Side Effects:
        - Uploads/overwrites a blob named `<path>.html` in the connected Blob store
        - Stores the returned public URL in KV under key `blob_url:{path}`
    """
    url = path_to_url[path]
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    html_bytes = resp.content

    # Filename inside the blob store
    blob_name = f"{path}.html"

    try:
        upload_resp = _upload_blob_bytes(blob_name, html_bytes)
        blob_url = upload_resp.get("url") or upload_resp.get("downloadUrl")
        if not blob_url:
            # Some versions of the wrapper return `url` in a nested object; try fallback
            blob_url = upload_resp.get("pathname")
        # Persist the blob URL in KV for quick lookup
        kv.set(f"blob_url:{path}", blob_url)
        return blob_url
    except Exception as e:
        logging.exception("Failed uploading to Vercel Blob: %s", e)
        # Fallback: store the HTML content in KV directly (small sites only).
        # WARNING: storing large HTML in Redis may hit maxmemory limits. Use with caution.
        kv.set(f"html_fallback:{path}", html_bytes.decode("utf-8"))
        # Also clear any blob_url so callers know to use the fallback
        kv.delete(f"blob_url:{path}")
        return "KV_FALLBACK"


def update_time(path: str) -> None:
    """
    Update the last refresh timestamp for a specific data path in UTC+8.

    This function updates the timestamp for the specified path with the current time
    and stores it in Vercel KV under the key `time:{path}`.

    Args:
        path: The data path to update (e.g., 'resolutions', 'ordinances').

    Returns:
        None
    """
    utc_plus_8 = timezone(timedelta(hours=8))
    current_time = datetime.now(utc_plus_8).isoformat()
    kv.set(f"time:{path}", current_time)


def get_time(path: str) -> Optional[str]:
    """
    Retrieve the last refresh timestamp for a specific data path from Vercel KV.

    Args:
        path: The data path to look up (e.g., 'resolutions', 'ordinances').

    Returns:
        The ISO-format timestamp string in UTC+8 if found, None otherwise.
    """
    return kv.get(f"time:{path}")


def _get_blob_url_from_kv(path: str) -> Optional[str]:
    """Helper: get the stored blob URL from KV for a given path."""
    return kv.get(f"blob_url:{path}")


def _get_html_from_blob_url(blob_url: str) -> Optional[str]:
    """Fetch the HTML text from a public blob URL via HTTP GET."""
    if not blob_url:
        return None
    r = requests.get(blob_url, timeout=20)
    if r.status_code != 200:
        # non-200 responses are returned as None
        return None
    return r.text


def get_html(path: str) -> Optional[str]:
    """
    Retrieve the current HTML for a path. Prefer the Blob url stored in KV. If the
    blob is not available, fall back to the KV-stored HTML (if present).

    Returns:
        HTML string or None if nothing is available.
    """
    blob_url = _get_blob_url_from_kv(path)
    if blob_url:
        html = _get_html_from_blob_url(blob_url)
        if html is not None:
            return html
    # Blob either missing or failed; try KV fallback (if exists)
    fallback = kv.get(f"html_fallback:{path}")
    return fallback


def update_if_needed(path: str, refresh_timer: timedelta = timedelta(days=1)) -> None:
    """
    Refresh HTML content if the cached version is outdated. Uses KV for timestamps
    and Vercel Blob for storing HTML.

    This function checks the last update timestamp for the specified path and
    refreshes the HTML content if the time elapsed since the last update is
    greater than or equal to the refresh_timer. If no timestamp exists, it
    refreshes immediately.
    """
    last_updated_str = get_time(path)
    if last_updated_str is None:
        # No record exists -> refresh now
        refresh_html(path)
        update_time(path)
        return

    last_updated = datetime.fromisoformat(last_updated_str)
    utc_plus_8 = timezone(timedelta(hours=8))
    current_time = datetime.now(utc_plus_8)
    if current_time - last_updated >= refresh_timer:
        refresh_html(path)
        update_time(path)
    return


def get_current_year() -> int:
    """
    Get the current year in UTC+8 (Philippine Time).

    Returns:
        The current year as an integer.
    """
    utc_plus_8 = timezone(timedelta(hours=8))
    return datetime.now(utc_plus_8).year


# Optional helper you can call from your endpoint to ensure availability and return HTML
def ensure_and_get(path: str, refresh_timer: timedelta = timedelta(days=1)) -> str:
    """
    Convenience wrapper: make sure content is up-to-date, then return the HTML.

    This is the function your FastAPI GET endpoint can call directly. It will
    try to keep memory usage low by reading HTML via HTTP from Blob.
    """
    try:
        update_if_needed(path, refresh_timer)
        html = get_html(path)
        if html is None:
            raise RuntimeError("No HTML available after update")
        return html
    except Exception as e:
        logging.exception("ensure_and_get failed for %s: %s", path, e)
        raise
