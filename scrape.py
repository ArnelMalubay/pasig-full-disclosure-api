import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime, timezone, timedelta

from requests.compat import numeric_types


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



def get_resolutions(start_year, end_year, query = None, num_results = None):
    update_if_needed("resolutions")
    with open("htmls/resolutions.html", "r", encoding = "utf-8") as f:
        soup = BeautifulSoup(f, "lxml")
    
    # Filter and extract across all years
    results = []
    
    # Loop through years from start_year to end_year (inclusive, descending)
    for year in range(start_year, end_year + 1):
        # Check if we've reached the desired number of results
        if num_results is not None and len(results) >= num_results:
            break
        
        # Find the section for this year
        id_to_use = f"cr-collapseOne-{year}"
        year_soup = soup.find(id = id_to_use)
        if year_soup is None:
            continue  # Skip this year if not found
        
        all_trs = year_soup.find_all('tr')
        
        # Process rows for this year
        for tr in all_trs:
            # Check if we've reached the desired number of results
            if num_results is not None and len(results) >= num_results:
                break
            
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
            results.append(data)
    last_updated = get_time("resolutions")
    return {
        "num_results": len(results),
        "last_updated": last_updated,
        "results": results,
    }

def get_ordinances(start_year, end_year, query = None, num_results = None):
    update_if_needed("ordinances")
    with open("htmls/ordinances.html", "r", encoding = "utf-8") as f:
        soup = BeautifulSoup(f, "lxml")
    
    # Filter and extract across all years
    results = []
    
    # Loop through years from start_year to end_year (inclusive, descending)
    for year in range(start_year, end_year + 1):
        # Check if we've reached the desired number of results
        if num_results is not None and len(results) >= num_results:
            break
        
        # Find the section for this year
        id_to_use = f"co-collapseTwo-{year}"
        year_soup = soup.find(id = id_to_use)
        if year_soup is None:
            continue  # Skip this year if not found
        
        all_trs = year_soup.find_all('tr')
        
        # Process rows for this year
        for tr in all_trs:
            # Check if we've reached the desired number of results
            if num_results is not None and len(results) >= num_results:
                break
            
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
            results.append(data)
    last_updated = get_time("ordinances")
    return {
        "num_results": len(results),
        "last_updated": last_updated,
        "results": results,
    }

def get_executive_orders(start_year, end_year, query = None, num_results = None):
    update_if_needed("executive-orders")
    with open("htmls/executive-orders.html", "r", encoding = "utf-8") as f:
        soup = BeautifulSoup(f, "lxml")
    
    headers = soup.find_all(class_ = "card-header")
    # Filter and extract across all years
    results = []
    
    # Loop through years from start_year to end_year (inclusive, descending)
    for year in range(start_year, end_year + 1):
        # Check if we've reached the desired number of results
        if num_results is not None and len(results) >= num_results:
            break
        
        # Find the section for this year
        year_header = [header for header in headers if str(year) in header.find('h2').string]
        if len(year_header) == 0:
            continue  # Skip this year if not found
        
        year_soup = year_header[0].next_sibling.next_sibling
        all_trs = year_soup.find_all('tr')
        
        # Process rows for this year
        for tr in all_trs:
            # Check if we've reached the desired number of results
            if num_results is not None and len(results) >= num_results:
                break
            
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
            results.append(data)
    last_updated = get_time("executive-orders")
    return {
        "num_results": len(results),
        "last_updated": last_updated,
        "results": results,
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


def get_bids_and_awards(category, query = None, num_results = None):
    update_if_needed("bids-and-awards")
    with open("htmls/bids-and-awards.html", "r", encoding = "utf-8") as f:
        soup = BeautifulSoup(f, "lxml")
    path = path_to_title[category]
    headers = soup.find_all(class_ = "col-md-12 text-center")
    for header in headers:
        if header.h1.string == path:
            trs = header.next_sibling.next_sibling.find_all('tr')
            break 
    results = []
    for tr in trs:
        # Check if we've reached the desired number of results
        if num_results is not None and len(results) >= num_results:
            break
            
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
        results.append(data)

    last_updated = get_time("bids-and-awards")
    return {
        "num_results": len(results),
        "last_updated": last_updated,
        "category": category,
        "results": results,
    }


def get_other_notices(query = None, num_results = None):
    update_if_needed("bids-and-awards")
    with open("htmls/bids-and-awards.html", "r", encoding = "utf-8") as f:
        soup = BeautifulSoup(f, "lxml")
    headers = soup.find_all(class_ = "col-md-12 text-center")
    for header in headers:
        if header.h1.string == 'Other Notices':
            trs = header.next_sibling.next_sibling.find_all('li')
            break 
    results = []
    for tr in trs:
        # Check if we've reached the desired number of results
        if num_results is not None and len(results) >= num_results:
            break
            
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
        results.append(data)

    last_updated = get_time("bids-and-awards")
    return {
        "num_results": len(results),
        "last_updated": last_updated,
        "results": results,
    }



results = get_other_notices()
print(results["num_results"])
print(results["last_updated"])
print(results["results"][0])
print(results["results"][-1])