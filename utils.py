"""
Utility functions for the Pasig Full Disclosure API.

This module provides functions for fetching, caching, and managing HTML data
from the Pasig City government website. All timestamps use UTC+8 (Philippine Time).
"""

import requests
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict


# Mapping of data paths to their corresponding URLs on the Pasig City website
path_to_url: Dict[str, str] = {
    "resolutions": "https://pasigcity.gov.ph/city-resolutions", 
    "ordinances": "https://pasigcity.gov.ph/city-ordinances", 
    "executive-orders": "https://pasigcity.gov.ph/executive-orders", 
    "bids-and-awards": "https://pasigcity.gov.ph/bids-and-awards"
}


def refresh_html(path: str) -> None:
    """
    Fetch HTML content from the Pasig City website and save it to a local file.
    
    Args:
        path: The data path (e.g., 'resolutions', 'ordinances', 'executive-orders', 'bids-and-awards').
              Must be a key in the path_to_url dictionary.
    
    Returns:
        None
    
    Side Effects:
        - Creates the 'htmls' directory if it doesn't exist
        - Creates or overwrites the file 'htmls/{path}.html' with fetched content
    """
    url = path_to_url[path]
    html = requests.get(url)
    
    # Create htmls folder if it doesn't exist
    os.makedirs("htmls", exist_ok = True)
    
    # Write the HTML content to file (creates new or replaces existing)
    filename = os.path.join("htmls", f"{path}.html")
    with open(filename, "w", encoding = "utf-8") as f:
        f.write(html.text)


def update_time(path: str) -> None:
    """
    Update the last refresh timestamp for a specific data path in UTC+8.
    
    This function reads the existing timestamps from 'last_updated.txt', updates
    the timestamp for the specified path with the current time, and writes all
    timestamps back to the file.
    
    Args:
        path: The data path to update (e.g., 'resolutions', 'ordinances').
    
    Returns:
        None
    
    Side Effects:
        - Creates or updates 'last_updated.txt' with the current timestamp
        - Preserves timestamps for other paths in the file
    """
    # Use UTC+8 timezone (Philippine Time)
    utc_plus_8 = timezone(timedelta(hours = 8))
    current_time = datetime.now(utc_plus_8).isoformat()
    
    # Read existing times
    times = {}
    if os.path.exists("last_updated.txt"):
        with open("last_updated.txt", "r", encoding = "utf-8") as f:
            for line in f:
                line = line.strip()
                if line and ":" in line:
                    key, value = line.split(":", 1)
                    times[key.strip()] = value.strip()
    
    # Update the time for the given path
    times[path] = current_time
    
    # Write all times back to file
    with open("last_updated.txt", "w", encoding = "utf-8") as f:
        for key, value in times.items():
            f.write(f"{key}: {value}\n")


def get_time(path: str) -> Optional[str]:
    """
    Retrieve the last refresh timestamp for a specific data path.
    
    Args:
        path: The data path to look up (e.g., 'resolutions', 'ordinances').
    
    Returns:
        The ISO-format timestamp string in UTC+8 if found, None otherwise.
    
    Example:
        >>> get_time("resolutions")
        '2025-11-05T17:29:40.443171+08:00'
    """
    with open("last_updated.txt", "r", encoding = "utf-8") as f:
        for line in f:
            line = line.strip()
            if line and ":" in line:
                key, value = line.split(":", 1)
                if key.strip() == path:
                    return value.strip()
    return None


def update_if_needed(path: str, refresh_timer: timedelta = timedelta(days = 1)) -> None:
    """
    Refresh HTML content if the cached version is outdated.
    
    This function checks the last update timestamp for the specified path and
    refreshes the HTML content if the time elapsed since the last update is
    greater than or equal to the refresh_timer. If no timestamp exists, it
    refreshes immediately.
    
    Args:
        path: The data path to check and potentially refresh.
        refresh_timer: The minimum time between refreshes (default: 1 day).
    
    Returns:
        None
    
    Side Effects:
        - May fetch new HTML content and update the local cache
        - May update the timestamp in 'last_updated.txt'
    
    Example:
        >>> # Refresh if older than 1 day (default)
        >>> update_if_needed("resolutions")
        >>> 
        >>> # Refresh if older than 12 hours
        >>> update_if_needed("ordinances", refresh_timer = timedelta(hours = 12))
    """
    # Get the last updated time for the path
    last_updated_str = get_time(path)
    
    # If no record exists, refresh immediately
    if last_updated_str is None:
        refresh_html(path)
        update_time(path)
        return
    
    # Parse the last updated time
    last_updated = datetime.fromisoformat(last_updated_str)
    
    # Get current time in UTC+8
    utc_plus_8 = timezone(timedelta(hours = 8))
    current_time = datetime.now(utc_plus_8)
    
    # Check if refresh is needed
    time_difference = current_time - last_updated
    
    if time_difference >= refresh_timer:
        refresh_html(path)
        update_time(path)
    return


def get_current_year() -> int:
    """
    Get the current year in UTC+8 (Philippine Time).
    
    This ensures the year is always calculated based on Philippine Time,
    regardless of the server's local timezone.
    
    Returns:
        The current year as an integer.
    
    Example:
        >>> get_current_year()
        2025
    """
    # Use UTC+8 timezone (Philippine Time)
    utc_plus_8 = timezone(timedelta(hours = 8))
    current_time = datetime.now(utc_plus_8)
    return current_time.year