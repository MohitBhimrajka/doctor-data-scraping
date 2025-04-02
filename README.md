# Doctor Search Application

This application allows users to search for doctors across multiple sources based on city and specialization.

## Components

The application consists of two main components:

1. **Backend API** (FastAPI): Handles doctor searches across multiple data sources.
2. **Frontend** (HTML/JavaScript): Provides an intuitive user interface for searching doctors.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Node.js 14 or higher
- npm (comes with Node.js)

### Installation and Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd doctor-search-app
   ```

2. Set up Python environment and install backend dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up frontend dependencies:
   ```
   cd frontend
   npm install
   cd ..
   ```

4. Create a `.env` file in the root directory with the following variables:
   ```
   GEMINI_API_KEY=your_api_key
   ```

5. Create a `.env` file in the frontend directory with:
   ```
   BACKEND_API_URL=http://localhost:8000
   PORT=3000
   ```

### Running the Application Locally

1. Start the backend server:
   ```
   python server.py
   ```

2. In a separate terminal, start the frontend server:
   ```
   cd frontend
   npm run dev
   ```

3. Access the application in your browser at `http://localhost:3000`

## API Endpoints

The backend provides the following API endpoints:

- `POST /api/search`: Search for doctors in a specific city with a specific specialization
- `POST /api/search/countrywide`: Search for doctors across all of India
- `POST /api/search/tier`: Search for doctors in a specific city tier (tier1, tier2, tier3)
- `POST /api/search/custom`: Search for doctors in a list of specified cities
- `GET /health`: Health check endpoint

## Deployment

The application is configured for deployment on Render.com using the `render.yaml` file.

### Render Deployment Steps

1. Fork or copy this repository to your own GitHub account.
2. Create a new Web Service on Render and select your repository.
3. Choose "Use render.yaml" when prompted.
4. Set the environment variables as needed in the Render dashboard.

## Architecture

- The backend uses FastAPI to provide API endpoints for doctor searches.
- The frontend is built using HTML, CSS, and JavaScript, providing a responsive user interface.
- Communication between frontend and backend is handled via RESTful API calls.

## Directory Structure

```
doctor-search-app/
├── frontend/                # HTML/JavaScript frontend
│   ├── public/              # Public assets
│   │   ├── index.html       # Main HTML file
│   │   ├── styles.css       # CSS styles
│   │   └── app.js           # JavaScript application logic
│   ├── assets/              # Static assets (images, etc.)
│   ├── server.js            # Express server for frontend
│   └── package.json         # Node.js dependencies
├── .env                     # Environment variables
├── server.py                # FastAPI backend server
├── doctor_search_enhanced.py # Core search functionality
├── render.yaml              # Render deployment configuration
├── requirements.txt         # Python dependencies
└── run_render.sh            # Script for running on Render
```

## License

This project is licensed under the MIT License - see the LICENSE file for details. 