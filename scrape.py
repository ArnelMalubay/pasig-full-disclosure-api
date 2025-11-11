"""
FastAPI application for the Pasig Full Disclosure API.

This API provides access to Pasig City government documents including resolutions,
ordinances, executive orders, and bids & awards information.
"""

from fastapi import FastAPI, HTTPException, Query, Path
from typing import Optional, List, Dict, Any
from bs4 import BeautifulSoup
from utils import get_current_year, update_if_needed, get_time
import os


app = FastAPI(
    title = "Pasig Full Disclosure API",
    description = "API for accessing Pasig City government transparency documents",
    version = "1.0.0"
)


# Valid paths for data retrieval
VALID_PATHS = ["resolutions", "ordinances", "executive-orders"]


@app.get("/", summary = "API Information", tags = ["Root"])
async def root() -> Dict[str, Any]:
    """
    Get API information and available endpoints.
    """
    return {
        "name": "Pasig Full Disclosure API",
        "version": "1.0.0",
        "description": "API for accessing Pasig City government transparency documents",
        "endpoints": {
            "documents": "GET /{path}?start_year=2000&end_year=2025&query=&skip=0&top=500",
            "bids_and_awards": "GET /bids-and-awards/{category}?query=&skip=0&top=500"
        },
        "valid_paths": VALID_PATHS,
        "valid_categories": list(path_to_title.keys())
    }

# Mapping of bids & awards categories to their display titles
path_to_title: Dict[str, str] = {
    "annual-procurement-plan": "Annual Procurement Plan",
    "procurement-monitoring-report": "Procurement Monitoring Report",
    "bid-bulletin": "Bid Bulletin",
    "invitation-to-bid": "Invitation to Bid",
    "request-for-quotation": "Request for Quotation",
    "notice-of-awards": "Notice of Awards",
    "notice-to-proceed": "Notice to Proceed",
    "purchase-order-of-contract": "Purchase Order of Contract",
    "other-notices": "Other Notices"
}


@app.get(
    "/{path}",
    summary = "Get documents by path and year range",
    response_description = "List of documents with pagination metadata"
)
async def get_data(
    path: str = Path(..., description = "Document type (resolutions, ordinances, executive-orders)"),
    start_year: int = Query(2000, ge = 2000, le = 2100, description = "Starting year for document search"),
    end_year: Optional[int] = Query(None, ge = 2000, le = 2100, description = "Ending year for document search (defaults to current year)"),
    query: Optional[str] = Query(None, description = "Search query to filter documents by title"),
    skip: int = Query(0, ge = 0, description = "Number of results to skip for pagination"),
    top: int = Query(500, ge = 1, le = 1000, description = "Maximum number of results to return")
) -> Dict[str, Any]:
    """
    Retrieve documents by path (resolutions, ordinances, executive-orders) with optional filtering.
    
    Returns paginated results with metadata including total count, allowing clients to
    implement pagination by adjusting skip and top parameters.
    """
    # Validate path
    if path not in VALID_PATHS:
        raise HTTPException(
            status_code = 404,
            detail = f"Path '{path}' not found. Valid paths: {', '.join(VALID_PATHS)}"
        )
    
    # Set default end_year if not provided
    if end_year is None:
        end_year = get_current_year()
    
    # Validate year range
    if start_year > end_year:
        raise HTTPException(
            status_code = 400,
            detail = "start_year cannot be greater than end_year"
        )
    
    # Check if HTML file exists
    html_file = f"htmls/{path}.html"
    if not os.path.exists(html_file):
        raise HTTPException(
            status_code = 503,
            detail = f"Data for '{path}' is not yet available. Please try again later."
        )
    
    try:
        update_if_needed(path)
        with open(html_file, "r", encoding = "utf-8") as f:
            soup = BeautifulSoup(f, "lxml")
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = f"Error reading data: {str(e)}"
        )
    
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


@app.get(
    "/bids-and-awards/{category}",
    summary = "Get bids and awards documents by category",
    response_description = "List of bids and awards documents with pagination metadata"
)
async def get_bids_and_awards(
    category: str = Path(..., description = "Category of bids/awards document"),
    query: Optional[str] = Query(None, description = "Search query to filter documents by title"),
    skip: int = Query(0, ge = 0, description = "Number of results to skip for pagination"),
    top: int = Query(500, ge = 1, le = 1000, description = "Maximum number of results to return")
) -> Dict[str, Any]:
    """
    Retrieve bids and awards documents by category with optional filtering.
    
    Returns paginated results with metadata including total count, allowing clients to
    implement pagination by adjusting skip and top parameters.
    """
    # Validate category
    if category not in path_to_title:
        raise HTTPException(
            status_code = 404,
            detail = f"Category '{category}' not found. Valid categories: {', '.join(path_to_title.keys())}"
        )
    
    # Check if HTML file exists
    html_file = "htmls/bids-and-awards.html"
    if not os.path.exists(html_file):
        raise HTTPException(
            status_code = 503,
            detail = "Bids and awards data is not yet available. Please try again later."
        )
    
    try:
        update_if_needed("bids-and-awards")
        with open(html_file, "r", encoding = "utf-8") as f:
            soup = BeautifulSoup(f, "lxml")
    except Exception as e:
        raise HTTPException(
            status_code = 500,
            detail = f"Error reading data: {str(e)}"
        )
    
    path = path_to_title[category]
    tag_to_use = 'li' if category == 'other-notices' else 'tr'
    headers = soup.find_all(class_ = "col-md-12 text-center")
    
    trs = []
    for header in headers:
        if header.h1 and header.h1.string == path:
            trs = header.next_sibling.next_sibling.find_all(tag_to_use)
            break
    
    if not trs:
        raise HTTPException(
            status_code = 404,
            detail = f"No data found for category '{category}'"
        )
    
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


# Run the server if this script is executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host = "0.0.0.0", port = 8000)