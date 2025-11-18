# Pasig Full Disclosure API

A free-to-use REST API to access Pasig City government transparency documents including resolutions, ordinances, executive orders, and bids & awards information. This API scrapes and provides structured access to public documents from the [Pasig City government website](https://pasigcity.gov.ph).

## 🌐 Live Demo

**Deployed on HuggingFace Spaces:** [https://arnel8888-pasig-full-disclosure-api.hf.space](https://arnel8888-pasig-full-disclosure-api.hf.space)


## ✨ Features

- 📄 **Access to Public Documents**: Resolutions, ordinances, executive orders, and bids & awards
- 🔍 **Search Functionality**: Filter documents by keywords in titles
- 📅 **Year-based Filtering**: Query documents by year range
- 📊 **Pagination Support**: Efficient pagination with `skip` and `top` parameters
- 🕐 **Auto-refresh**: Automatically updates cached data when stale
- 🐳 **Dockerized**: Ready for containerized deployment
- 📝 **OpenAPI Documentation**: Interactive API docs with Swagger UI

## 📚 API Endpoints

### Base URL
```
http://localhost:7860  # Local development
# or
https://arnel8888-pasig-full-disclosure-api.hf.space  # Production
```

### 1. API Information
```http
GET /
```
Returns API information including available endpoints and valid paths/categories.

### 2. Get Documents by Path
```http
GET /{path}?start_year=2000&end_year=2025&query=&skip=0&top=500
```

**Path Parameters:**
- `path` (required): Document type
  - `resolutions`
  - `ordinances`
  - `executive-orders`

**Query Parameters:**
- `start_year` (optional, default: `2000`): Starting year for search (2000-2100)
- `end_year` (optional, default: current year): Ending year for search (2000-2100)
- `query` (optional): Search query to filter documents by title (case-insensitive)
- `skip` (optional, default: `0`): Number of results to skip for pagination
- `top` (optional, default: `500`, max: `1000`): Maximum number of results to return

**Example:**
```bash
# Get resolutions from 2023-2024
curl "https://arnel8888-pasig-full-disclosure-api.hf.space/resolutions?start_year=2023&end_year=2024"

# Search for "budget" in ordinances
curl "https://arnel8888-pasig-full-disclosure-api.hf.space/ordinances?query=budget&skip=0&top=10"

# Paginate through resolutions
curl "https://arnel8888-pasig-full-disclosure-api.hf.space/resolutions?skip=0&top=20"  # First page
curl "https://arnel8888-pasig-full-disclosure-api.hf.space/resolutions?skip=20&top=20"  # Second page
```

**Response:**
```json
{
  "num_results": 150,
  "skip": 0,
  "top": 20,
  "returned_results": 20,
  "last_updated": "2025-11-12T14:30:45.123456+08:00",
  "results": [
    {
      "year": 2024,
      "title": "Resolution No. 123 Series Of 2024: ...",
      "link": "https://assets.pasigcity.gov.ph/storage/resolution.pdf",
      "uuid": "abc123-def456-ghi789",
      "views": "150"
    }
  ]
}
```

### 3. Get Bids & Awards by Category
```http
GET /bids-and-awards/{category}?query=&skip=0&top=500
```

**Path Parameters:**
- `category` (required): Category of bids/awards document
  - `annual-procurement-plan`
  - `procurement-monitoring-report`
  - `bid-bulletin`
  - `invitation-to-bid`
  - `request-for-quotation`
  - `notice-of-awards`
  - `notice-to-proceed`
  - `purchase-order-of-contract`
  - `other-notices`

**Query Parameters:**
- `query` (optional): Search query to filter documents by title (case-insensitive)
- `skip` (optional, default: `0`): Number of results to skip for pagination
- `top` (optional, default: `500`, max: `1000`): Maximum number of results to return

**Example:**
```bash
# Get notice of awards
curl "https://arnel8888-pasig-full-disclosure-api.hf.space/bids-and-awards/notice-of-awards"

# Search for "construction" in invitations to bid
curl "https://arnel8888-pasig-full-disclosure-api.hf.space/bids-and-awards/invitation-to-bid?query=construction&top=10"
```

**Response:**
```json
{
  "num_results": 45,
  "skip": 0,
  "top": 10,
  "returned_results": 10,
  "last_updated": "2025-11-12T14:30:45.123456+08:00",
  "category": "notice-of-awards",
  "results": [
    {
      "title": "Notice of Award - Bridge Construction Project",
      "link": "https://assets.pasigcity.gov.ph/storage/noa/award123.pdf",
      "uuid": "noa123-abc456-def789",
      "views": "89"
    }
  ]
}
```

## 📖 Interactive Documentation

Visit the interactive API documentation:
- **Swagger UI**: `https://arnel8888-pasig-full-disclosure-api.hf.space/docs`
- **ReDoc**: `https://arnel8888-pasig-full-disclosure-api.hf.space/redoc`

## 🚀 Installation

### Prerequisites
- Python 3.9 or higher
- pip

### Local Setup

1. **Clone the repository**
```bash
git clone https://github.com/your-username/pasig-full-disclosure-api.git
cd pasig-full-disclosure-api
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python -m uvicorn app:app --host 0.0.0.0 --port 7860
```

4. **Access the API** (when running locally)
   - API: `http://localhost:7860`
   - Documentation: `http://localhost:7860/docs`
   
   Or use the live deployment:
   - API: `https://arnel8888-pasig-full-disclosure-api.hf.space`
   - Documentation: `https://arnel8888-pasig-full-disclosure-api.hf.space/docs`

## 🐳 Docker Setup

### Build the image
```bash
docker build -t pasig-full-disclosure-api .
```

### Run the container
```bash
docker run -p 7860:7860 pasig-full-disclosure-api
```

### Run with volume (to persist data)
```bash
docker run -p 7860:7860 -v $(pwd)/data:/app/data pasig-full-disclosure-api
```

## 📁 Project Structure

```
pasig-full-disclosure-api/
├── app.py              # FastAPI application and endpoints
├── utils.py            # Utility functions for scraping and caching
├── requirements.txt    # Python dependencies
├── Dockerfile          # Docker configuration
├── .dockerignore       # Docker ignore file
├── .gitignore         # Git ignore file
├── README.md          # This file
└── data/              # Cached HTML files and timestamps (auto-generated)
    ├── *.html         # Scraped HTML files
    └── last_updated.txt  # Timestamps for each data source
```

## 🔧 How It Works

1. **First Request**: The API checks if cached HTML files exist. If not, it fetches data from the Pasig City website.

2. **Caching**: HTML content is cached locally in the `data/` directory to reduce requests to the source website.

3. **Auto-refresh**: Cached data is automatically refreshed if it's older than 1 day (configurable).

4. **Data Extraction**: BeautifulSoup parses the HTML and extracts structured document information.

5. **Filtering & Pagination**: Results are filtered by query, year range, and paginated before returning.

## 🌟 Usage Examples

### Python
```python
import requests

# Get resolutions from 2024
response = requests.get("https://arnel8888-pasig-full-disclosure-api.hf.space/resolutions", params={
    "start_year": 2024,
    "end_year": 2024,
    "top": 10
})
data = response.json()
print(f"Found {data['num_results']} resolutions")
for result in data['results']:
    print(f"- {result['title']}")
```

### JavaScript/Node.js
```javascript
const fetch = require('node-fetch');

// Search for budget-related documents
const response = await fetch('https://arnel8888-pasig-full-disclosure-api.hf.space/resolutions?query=budget&top=5');
const data = await response.json();
console.log(`Found ${data.num_results} results`);
data.results.forEach(result => console.log(`- ${result.title}`));
```

### cURL
```bash
# Get all bids and awards categories
curl "https://arnel8888-pasig-full-disclosure-api.hf.space/bids-and-awards/notice-of-awards?top=5"

# Search with pagination
curl "https://arnel8888-pasig-full-disclosure-api.hf.space/resolutions?query=infrastructure&skip=0&top=10"
```

## 📝 Notes

- All timestamps use **UTC+8** (Philippine Time)
- The API automatically rebuilds cached data if the `data/` folder is empty
- Data is cached to respect the source website and improve response times
- Maximum 1000 results per request (`top` parameter)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is free to use. Data is sourced from the public Pasig City government website.

## 🙏 Credits

- **Data Source**: [Pasig City Government](https://pasigcity.gov.ph)
- Built with [FastAPI](https://fastapi.tiangolo.com/)
- HTML parsing with [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)

## 📞 Support

For issues or questions, please open an issue on the GitHub repository.

---

**Made with ❤️ for transparency and accessibility**
