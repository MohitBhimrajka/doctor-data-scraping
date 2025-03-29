# Doctor Search Application

A modern web application for searching and finding doctors across multiple sources, built with FastAPI, Streamlit, and the Gemini API.

## Project Structure

```
doctor-data-scraping/
├── streamlit-frontend/         # Frontend Streamlit application
│   ├── app_streamlit.py        # Main Streamlit application
│   ├── requirements.txt        # Frontend dependencies
│   ├── .env                    # Environment variables
│   └── assets/                 # Image assets
│       ├── Supervity_Black_Without_Background.png
│       └── Supervity_Icon.png
├── logs/                      # Application logs directory
├── doctor_search_enhanced.py   # Core search functionality
├── server.py                   # FastAPI backend server
├── requirements.txt            # Backend Python dependencies
├── run_app.sh                  # Script to run both frontend and backend
├── .env                       # Root environment variables
└── GEMINI_API_KEY_GUIDE.md    # Guide for obtaining API key
```

## Features

- 🔍 Search doctors by city and specialization
- 📊 Clean and intuitive user interface
- ⭐ Display results with ratings and reviews
- 📥 Export results to CSV
- 🎨 Modern UI with Supervity brand colors
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
- Google Gemini API
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

### Backend Setup
1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Start the FastAPI server:
```bash
python server.py
```
The server will run on http://localhost:8000

### Frontend Setup
1. Navigate to the frontend directory:
```bash
cd streamlit-frontend
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Start the Streamlit server:
```bash
streamlit run app_streamlit.py
```
The application will be available at http://localhost:8501

### Running Both Services Together
For convenience, you can use the provided shell script to run both the backend and frontend:
```bash
./run_app.sh
```

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
      "source": "string",
      "specialization": "string",
      "city": "string",
      "timestamp": "string"
    }
  ],
  "metadata": {
    "total": number,
    "timestamp": "string",
    "query": {
      "city": "string",
      "specialization": "string"
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **"Configuration validation failed" error**:
   - Make sure you have set a valid `GEMINI_API_KEY` in your `.env` file
   - Ensure the API key has proper permissions and hasn't expired

2. **Backend connection issues from frontend**:
   - Verify the backend is running
   - Check that `BACKEND_API_URL` in the frontend's `.env` matches where the backend is running

## Data Sources
The application searches across multiple sources:
- Practo
- JustDial
- Hospital Websites
- General Medical Directories

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
MIT License

## Acknowledgments
- Google Gemini API for search capabilities
- FastAPI team for the efficient backend framework
- Streamlit team for the intuitive UI framework 