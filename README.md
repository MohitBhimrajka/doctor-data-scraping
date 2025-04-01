# Doctor Search API

A FastAPI-based backend service for searching and retrieving doctor information using Google's Gemini AI.

## Features

- Search doctors by specialization and location
- Verify doctor information from multiple sources
- Store and retrieve doctor data
- Get doctor statistics
- Pagination support
- Rate limiting and caching
- Comprehensive error handling

## Prerequisites

- Python 3.8+
- Google Gemini API key
- Virtual environment (recommended)

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd doctor-data-scraping
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory:
```env
GEMINI_API_KEY=your_api_key_here
```

## Running the Application

1. Start the server:
```bash
uvicorn backend.main:app --reload
```

2. Access the API documentation:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## API Endpoints

### Search Doctors
```http
POST /api/v1/search
```

Parameters:
- `specialization` (required): Doctor's specialization
- `city` (optional): City name
- `country` (optional): Country name (defaults to India)
- `tiers` (optional): List of city tiers
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Results per page (default: 10, max: 100)

### Get Doctor Details
```http
GET /api/v1/doctor/{doctor_id}
```

### Get Statistics
```http
GET /api/v1/stats
```

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black .
```

## Project Structure

```
backend/
├── api/
│   └── routes.py
├── models/
│   ├── doctor.py
│   └── city.py
├── services/
│   ├── discovery.py
│   ├── verification.py
│   └── database.py
├── utils/
│   ├── client.py
│   └── city_cache.py
├── config.py
└── main.py
```

## Error Handling

The API includes comprehensive error handling for:
- Validation errors (422)
- Not found errors (404)
- Server errors (500)
- Rate limiting (429)

## Performance Considerations

- Concurrent processing for multiple sources
- In-memory caching for city data
- Rate limiting for API calls
- Pagination for large result sets
- Efficient data storage and retrieval

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 