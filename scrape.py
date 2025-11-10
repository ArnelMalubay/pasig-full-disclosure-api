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


def get_data(path, start_year = 2000, end_year = 2025, query = None, skip = 0, top = 500):
    update_if_needed(path)
    with open(f"htmls/{path}.html", "r", encoding = "utf-8") as f:
        soup = BeautifulSoup(f, "lxml")
    
    headers = soup.find_all(class_ = "card-header")
    # Filter and extract across all years - collect ALL results first
    all_results = []
    
    # Loop through years from start_year to end_year (inclusive)
    for year in range(start_year, end_year + 1):
        # Find the section for this year
        year_header = [header for header in headers if str(year) in header.find('h2').string]
        if len(year_header) == 0:
            continue  # Skip this year if not found
        
        year_soup = year_header[0].next_sibling.next_sibling
        all_trs = year_soup.find_all('tr')
        
        # Process rows for this year
        for tr in all_trs:
            a_tag = tr.find('a')
            if not a_tag:  # Skip if no 'a' tag
                continue
            
            # Extract title first to check query
            title = a_tag.get_text(strip = True)
            
            # Filter by query if provided
            if query is not None and query.lower() not in title.lower():
                continue
            
            # Extract remaining data (all Tag methods, no re-parsing needed)
            tds = tr.find_all('td')
            data = {
                'year': year,
                'title': title,
                'link': a_tag.get('href'),
                'uuid': a_tag.get('data-uuid'),
                'views': tds[1].get_text(strip = True) if len(tds) > 1 else None,
            }
            all_results.append(data)
    
    # Apply pagination: skip and top
    total_count = len(all_results)
    paginated_results = all_results[skip:skip + top]
    
    last_updated = get_time(path)
    return {
        "num_results": total_count,
        "skip": skip,
        "top": top,
        "returned_results": len(paginated_results),
        "last_updated": last_updated,
        "results": paginated_results,
    }

path_to_title = {"annual-procurement-plan" : "Annual Procurement Plan",
                 "procurement-monitoring-report" : "Procurement Monitoring Report",
                 "bid-bulletin" : "Bid Bulletin",
                 "invitation-to-bid" : "Invitation to Bid",
                 "request-for-quotation" : "Request for Quotation",
                 "notice-of-awards" : "Notice of Awards",
                 "notice-to-proceed" : "Notice to Proceed",
                 "purchase-order-of-contract" : "Purchase Order of Contract",
                 "other-notices" : "Other Notices"}


def get_bids_and_awards(category, query = None, skip = 0, top = 500):
    update_if_needed("bids-and-awards")
    with open("htmls/bids-and-awards.html", "r", encoding = "utf-8") as f:
        soup = BeautifulSoup(f, "lxml")
    path = path_to_title[category]
    tag_to_use = 'li' if category == 'other-notices' else 'tr'
    headers = soup.find_all(class_ = "col-md-12 text-center")
    for header in headers:
        if header.h1.string == path:
            trs = header.next_sibling.next_sibling.find_all(tag_to_use)
            break
    
    # Collect all results first
    all_results = []
    for tr in trs:
        a_tag = tr.find('a')
        if not a_tag:  # Skip if no 'a' tag
            continue
            
        # Extract title first to check query
        title = a_tag.get_text(strip = True)
            
        # Filter by query if provided
        if query is not None and query.lower() not in title.lower():
            continue
            
        # Extract remaining data (all Tag methods, no re-parsing needed)
        tds = tr.find_all('td')
        data = {
            'title': title,
            'link': a_tag.get('href'),
            'uuid': a_tag.get('data-uuid'),
            'views': tds[1].get_text(strip = True) if len(tds) > 1 else None,
        }
        all_results.append(data)
    
    # Apply pagination
    total_count = len(all_results)
    paginated_results = all_results[skip:skip + top]

    last_updated = get_time("bids-and-awards")
    return {
        "num_results": total_count,
        "skip": skip,
        "top": top,
        "returned_results": len(paginated_results),
        "last_updated": last_updated,
        "category": category,
        "results": paginated_results,
    }

results = get_bids_and_awards("other-notices", query = 'pasig lgu')
print(f"Total matching results: {results['num_results']}")
print(f"Skip: {results['skip']}, Top: {results['top']}")
print(f"Returned: {len(results['results'])} results")
print(f"Last updated: {results['last_updated']}")
print('-' * 100)
if len(results['results']) > 0:
    print(f"First result: {results['results'][0]}")
    print(f"Last result: {results['results'][-1]}")