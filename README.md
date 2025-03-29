# Doctor Search Application

A streamlined web application for finding doctors with core information (name, rating, reviews, and locations) across multiple sources, built with FastAPI, Streamlit, and the Gemini API.

## Project Structure

```
doctor-data-scraping/
├── streamlit-frontend/         # Frontend Streamlit application
│   ├── app_streamlit.py        # Main Streamlit application
│   └── .env                    # Frontend environment variables
├── logs/                       # Application logs directory
├── doctor_search_enhanced.py   # Core search functionality
├── server.py                   # FastAPI backend server
├── requirements.txt            # Python dependencies (backend & frontend)
├── run_app.sh                  # Script to run both frontend and backend
├── .env                        # Root environment variables
└── GEMINI_API_KEY_GUIDE.md     # Guide for obtaining API key
```

## Features

- 🔍 Search doctors by city and specialization
- 📱 Access core information: name, rating, reviews, and accurate locations
- 🚀 High throughput data collection through optimized Gemini API usage
- 📊 Clean and intuitive user interface
- 📥 Export results to CSV or JSON
- 🔄 Asynchronous processing for better performance

## Technology Stack

### Frontend
- Streamlit
- Python 3.8+
- Pandas
- httpx

### Backend
- FastAPI
- Python 3.8+
- Google Gemini API (Gemini-2.0-flash model)
- SQLite Database

## Setup

### Prerequisites
- Python 3.8+
- Google Gemini API Key (required for the backend to work)

### Environment Variables
Create a `.env` file in the root directory:
```env
# Required - obtain your API key from https://ai.google.dev/
GEMINI_API_KEY=your_gemini_api_key_here  

# Other configuration
FRONTEND_URL=http://localhost:8501
BACKEND_API_URL=http://localhost:8000
```

⚠️ **Important**: You must replace `your_gemini_api_key_here` with your actual Gemini API key, or the application will not work.

### Installation and Running
The application uses a single requirements file for both frontend and backend dependencies:

1. Install all dependencies:
```bash
pip install -r requirements.txt
```

2. Run both services with the provided script:
```bash
./run_app.sh
```

The backend will run on http://localhost:8000 and the frontend will be available at http://localhost:8501

## API Endpoints

### `/api/search` (POST)
Search for doctors based on city and specialization.

Request body:
```json
{
  "city": "string",
  "specialization": "string"
}
```

Response:
```json
{
  "success": true,
  "data": [
    {
      "name": "string",
      "rating": number,
      "reviews": number,
      "locations": ["string"],
      "specialization": "string",
      "city": "string",
      "contributing_sources": ["string"],
      "timestamp": "string"
    }
  ],
  "metadata": {
    "total": number,
    "timestamp": "string",
    "query": {
      "city": "string",
      "specialization": "string"
    },
    "sources_queried": ["string"],
    "search_duration": number
  }
}
```

## Troubleshooting

### Database Schema Errors

If you see an error such as:
```
ERROR - Search error: table doctors has no column named locations
```

This indicates a mismatch between the database schema defined in the code and the actual structure of the `doctors.db` file. The application uses SQLite with a `CREATE TABLE IF NOT EXISTS` statement which won't modify an existing table structure.

**Solution**: Delete the existing `doctors.db` file. A new database with the correct schema will be created automatically when you run the application again.

```bash
# From the project root directory
rm doctors.db
```

The updated `run_app.sh` script will detect if `doctors.db` exists and prompt you to delete it if necessary.

### API Connection Issues

If the frontend shows a connection error to the backend:

1. Verify that the backend service is running (check for FastAPI logs in terminal)
2. Ensure the `.env` file in the `streamlit-frontend` directory has the correct `BACKEND_API_URL` setting
3. Check if any firewall or network settings are blocking the connection

### No Search Results

If your search completes but returns no doctors:

1. Verify that you've entered a valid city and specialization
2. Check the logs for any specific errors during the search process
3. Try a different combination of city and specialization
4. Check the Google API key validity and quota limits

## Data Sources
The application searches across multiple sources:
- Practo
- JustDial
- General web search
- Hospital websites
- Social proof & review sites

## License
MIT License

## Acknowledgments
- Google Gemini API for search capabilities
- FastAPI team for the efficient backend framework
- Streamlit team for the intuitive UI framework 