# Supervity Doctor Search - Streamlit Frontend

This is a Streamlit-based frontend for the Supervity Doctor Search application. It connects to the existing FastAPI backend to search for doctors and display results.

## Project Structure

```
streamlit-frontend/
├── app_streamlit.py        # Main Streamlit application
├── requirements.txt        # Frontend dependencies
├── .env                    # Environment variables
└── assets/                 # Image assets
    ├── Supervity_Black_Without_Background.png
    └── Supervity_Icon.png
```

## Prerequisites

- Python 3.8 or higher
- [Streamlit](https://streamlit.io/)
- [httpx](https://www.python-httpx.org/)
- [pandas](https://pandas.pydata.org/)
- [python-dotenv](https://github.com/theskumar/python-dotenv)

## Setup

1. Make sure the backend server is running
2. Install the required dependencies:

```bash
cd streamlit-frontend
pip install -r requirements.txt
```

3. Verify your environment variables in the `.env` file:

```
BACKEND_API_URL=http://localhost:8000
```

## Running the Application

To run the Streamlit frontend:

```bash
cd streamlit-frontend
streamlit run app_streamlit.py
```

This will start the Streamlit server, typically on port 8501. Open your browser and navigate to:

```
http://localhost:8501
```

## Features

- Search for doctors by city and specialization
- View results in a clean, tabular format
- Download search results as CSV
- Visual indicators for loading state
- Error handling and user feedback
- Supervity branding and styling

## Troubleshooting

If you encounter connection issues with the backend:

1. Make sure the FastAPI backend is running (`python server.py`)
2. Verify the BACKEND_API_URL in your .env file
3. Check the logs in `streamlit_app.log` for error details 