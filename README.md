# Doctor Search Application

A modern web application for searching and finding doctors across multiple sources, built with Next.js, FastAPI, and the Gemini API.

## Project Structure

```
doctor-data-scraping/
├── doctor-search-ui/           # Frontend Next.js application
│   ├── app/                    # Next.js app directory
│   │   ├── api/               # API routes
│   │   └── page.tsx           # Main page component
│   ├── types/                 # TypeScript type definitions
│   ├── public/                # Static assets
│   └── tailwind.config.ts     # Tailwind CSS configuration
├── doctor_search_enhanced.py   # Core search functionality
├── server.py                  # FastAPI backend server
└── requirements.txt           # Python dependencies
```

## Features

- 🔍 Search doctors by city and specialization
- 📊 Real-time search progress tracking
- ⭐ Sort results by rating, reviews, or name
- 📥 Export results to CSV
- 🎨 Modern UI with Supervity brand colors
- 🔄 Asynchronous processing for better performance

## Technology Stack

### Frontend
- Next.js 14
- TypeScript
- Tailwind CSS
- React Hooks

### Backend
- FastAPI
- Python 3.8+
- Google Gemini API
- SQLite Database

## Setup

### Prerequisites
- Node.js 18+
- Python 3.8+
- Google Gemini API Key

### Environment Variables
Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_api_key_here
```

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
cd doctor-search-ui
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```
The application will be available at http://localhost:3000

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
[
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
]
```

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
- Next.js team for the amazing framework
- FastAPI team for the efficient backend framework 