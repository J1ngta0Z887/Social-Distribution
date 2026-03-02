# API Documentation

## Overview

Base URL: `/api`  
API Format:  `json`
Authentication: Django user based.
---



### List All Authors
Endpoint: `GET /authors`
Requires Authentication?: No

Returns a paginated list of all authors in the system.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number |
| `size` | integer | 10 | Items per page |

**Example Request:**
```http
GET /authors?page=1&size=5
```

**Example Response:**
```json
{
  "type": "authors",
  "page": 1,
  "size": 5,
  "authors": [
    {
      "type": "author",
      "id": "https://example.com/authors/1",
      "host": "https://example.com/api",
      "displayName": "authors name",
      "bio": "authors detailed bio",
      "github": "https://github.com/johndoe",
      "profileImage": "https://example.com/images/john.jpg",
      "web": "https://example.com/authors/author%20name
    }
  ]
}
```