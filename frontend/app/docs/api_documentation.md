# Doctor Discovery API Documentation

## Overview

The Doctor Discovery API provides endpoints for searching doctors, retrieving doctor details, and accessing statistics. This documentation outlines the available endpoints, request/response formats, and usage guidelines.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

Currently, the API does not require authentication. Future versions may implement API key authentication.

## Endpoints

### Search Doctors

```http
GET /search
```

Search for doctors based on various criteria.

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| specialization | string | Yes | Doctor specialization |
| city | string | No | City name (for single city search) |
| country | string | No | Country name (default: "India") |
| tiers | array | No | List of city tiers [1,2,3] |
| page | integer | No | Page number (default: 1) |
| page_size | integer | No | Results per page (default: 10) |

#### Response

```json
{
    "doctors": [
        {
            "id": "string",
            "name": "string",
            "specialization": "string",
            "city": "string",
            "city_tier": "integer",
            "rating": "float",
            "reviews": "integer",
            "confidence": "float",
            "experience": "integer",
            "verified_sources": ["string"],
            "profile_urls": ["string"],
            "last_updated": "datetime"
        }
    ],
    "total": "integer",
    "page": "integer",
    "page_size": "integer"
}
```

### Get Doctor Details

```http
GET /doctor/{doctor_id}
```

Retrieve detailed information about a specific doctor.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| doctor_id | string | Yes | Unique doctor identifier |

#### Response

```json
{
    "id": "string",
    "name": "string",
    "specialization": "string",
    "city": "string",
    "city_tier": "integer",
    "rating": "float",
    "reviews": "integer",
    "confidence": "float",
    "experience": "integer",
    "verified_sources": ["string"],
    "profile_urls": ["string"],
    "last_updated": "datetime",
    "practice_locations": [
        {
            "city": "string",
            "city_tier": "integer",
            "address": "string"
        }
    ],
    "education": [
        {
            "degree": "string",
            "institution": "string",
            "year": "integer"
        }
    ],
    "specializations": ["string"]
}
```

### Get Statistics

```http
GET /stats
```

Retrieve statistics about the doctor database.

#### Response

```json
{
    "total_doctors": "integer",
    "total_specializations": "integer",
    "total_cities": "integer",
    "average_rating": "float",
    "average_reviews": "integer",
    "top_specializations": [
        {
            "name": "string",
            "count": "integer"
        }
    ],
    "top_cities": [
        {
            "name": "string",
            "count": "integer"
        }
    ],
    "rating_distribution": {
        "1-2": "integer",
        "2-3": "integer",
        "3-4": "integer",
        "4-5": "integer"
    },
    "city_tier_distribution": {
        "1": "integer",
        "2": "integer",
        "3": "integer"
    }
}
```

## Error Handling

### Error Response Format

```json
{
    "error": {
        "code": "string",
        "message": "string",
        "details": "object"
    }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

## Rate Limiting

- 100 requests per minute per IP
- 1000 requests per hour per IP

## Caching

- Search results are cached for 5 minutes
- Doctor details are cached for 1 hour
- Statistics are cached for 1 day

## Best Practices

1. **Request Optimization**
   - Use appropriate page sizes
   - Implement client-side caching
   - Batch requests when possible

2. **Error Handling**
   - Implement exponential backoff
   - Handle rate limiting
   - Validate responses

3. **Performance**
   - Use compression
   - Minimize payload size
   - Cache responses

## Example Usage

### Python

```python
import httpx
import asyncio

async def search_doctors(specialization: str, city: str = None):
    async with httpx.AsyncClient() as client:
        params = {
            "specialization": specialization,
            "city": city
        }
        response = await client.get("http://localhost:8000/api/v1/search", params=params)
        return response.json()

# Usage
async def main():
    results = await search_doctors("Cardiologist", "Mumbai")
    print(results)

asyncio.run(main())
```

### JavaScript

```javascript
async function searchDoctors(specialization, city = null) {
    const params = new URLSearchParams({
        specialization: specialization,
        ...(city && { city: city })
    });
    
    const response = await fetch(`http://localhost:8000/api/v1/search?${params}`);
    return response.json();
}

// Usage
searchDoctors("Cardiologist", "Mumbai")
    .then(results => console.log(results))
    .catch(error => console.error(error));
```

## Versioning

The API is versioned through the URL path:
- Current version: v1
- Future versions will be available at v2, v3, etc.

## Changelog

### v1.0.0
- Initial release
- Basic search functionality
- Doctor details endpoint
- Statistics endpoint

## Future Enhancements

1. **Authentication**
   - API key support
   - OAuth integration
   - Rate limiting per user

2. **New Endpoints**
   - Doctor comparison
   - Advanced filtering
   - Bulk operations

3. **Performance**
   - GraphQL support
   - WebSocket updates
   - Real-time statistics 