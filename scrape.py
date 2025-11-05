import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timezone, timedelta


path_to_url = {"resolutions" : "https://pasigcity.gov.ph/city-resolutions", 
               "ordinances" : "https://pasigcity.gov.ph/city-ordinances", 
               "executive-orders" : "https://pasigcity.gov.ph/executive-orders", 
               "bids-and-awards" : "https://pasigcity.gov.ph/bids-and-awards"}

def refresh_html(path):
    url = path_to_url[path]
    html = requests.get(url)
    
    # Create htmls folder if it doesn't exist
    os.makedirs("htmls", exist_ok = True)
    
    # Write the HTML content to file (creates new or replaces existing)
    filename = os.path.join("htmls", f"{path}.html")
    with open(filename, "w", encoding = "utf-8") as f:
        f.write(html.text)

def update_time(path):
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

def get_time(path):
    with open("last_updated.txt", "r", encoding = "utf-8") as f:
        for line in f:
            line = line.strip()
            if line and ":" in line:
                key, value = line.split(":", 1)
                if key.strip() == path:
                    return value.strip()
    return None

def update_if_needed(path, refresh_timer = timedelta(days = 1)):
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

