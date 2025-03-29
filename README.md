# Doctor Search Application

A streamlined web application for finding doctors with core information (name, rating, reviews, and locations) across multiple sources, built with FastAPI, Streamlit, and the Gemini API.

## Project Structure

```
doctor-data-scraping/
├── streamlit-frontend/         # Frontend Streamlit application
│   ├── app_streamlit.py        # Main Streamlit application
│   ├── assets/                 # Branding assets (logos, icons)
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
- 🎨 Modern and responsive UI with animations and Supervity branding
- 📊 Clean and intuitive user interface
- 📤 Export results to Excel with professional formatting
- 🔄 Asynchronous processing for better performance
- ✨ Smart validation for rare specialists and location detection

## Technology Stack

### Frontend
- Streamlit with custom CSS and animations
- Streamlit-Lottie for engaging animations
- Python 3.8+
- Pandas
- XlsxWriter for Excel export
- httpx for async API calls

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

The script will automatically:
- Delete any existing database to ensure schema consistency
- Set up the environment
- Install dependencies
- Run validation tests
- Start both the backend and frontend services

The backend will run on http://localhost:8000 and the frontend will be available at http://localhost:8501

### Branding Customization

To customize the Supervity branding:

1. Add your logo files to the `streamlit-frontend/` directory:
   - `logo.png` - For the main application logo
   - `icon.png` - For the browser tab favicon

The application is configured with Supervity's brand colors (primary: #000b37).

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

## UI Features

### Enhanced User Experience
- **Animations**: Smooth transitions and loading animations
- **Branding**: Consistent Supervity branding throughout the application
- **Responsive Design**: Adapts to different screen sizes
- **Visual Feedback**: Clear indicators for search progress and results

### Search Capabilities
- **Predefined Specializations**: Choose from a curated list of medical specialties
- **Custom Specializations**: Enter specific medical fields not in the predefined list
- **Smart Results**: Intelligent filtering of results to provide the most relevant doctors

### Results Display
- **Sortable Data**: Sort doctors by rating or number of reviews
- **Detailed Information**: View primary and secondary practice locations
- **Source Tracking**: See which sources contributed to each doctor's information

### Excel Export
- **Professional Formatting**: Branded Excel exports with proper formatting
- **Comprehensive Data**: All doctor details included in the export file
- **One-Click Download**: Prominently displayed download button

## Troubleshooting

### Database Schema Errors

The application now automatically deletes and recreates the database when you run `run_app.sh`, so database schema errors should be eliminated.

If you're running the components individually and see an error such as:
```
ERROR - Search error: table doctors has no column named locations
```

Simply delete the existing `doctors.db` file:
```bash
# From the project root directory
rm doctors.db
```

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

### Missing Animations or UI Elements

If some UI elements or animations are not displaying correctly:

1. Ensure all dependencies were installed correctly
2. Check that you have internet access (some animations load from external sources)
3. Verify that your browser supports the CSS animations used

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